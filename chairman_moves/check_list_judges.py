import re
from itertools import combinations
from queries import general_queries
from queries import chairman_queries
import config
import pymysql

async def check_list(text, user_id):
    try:
        s = ''
        flag1, flag2, flag3, flag4, flag5, flag6, flag7 = 0, 0, 0, 0, 0, 0, 0
        active_comp = await general_queries.get_CompId(user_id)
        const = await general_queries.get_tournament_lin_const(active_comp)
        judges_free = await general_queries.get_judges_free(active_comp)
        judges_free = [[i['lastName'], i['firstName'], i['bookNumber']] for i in judges_free]


        # Разбиваем текст сообщения на площадки по переносам строки, у строк с судьями по краям обрезаем переносы/пробелы/точки
        areas = re.split('\n\s{0,}\n', text)
        areas = [re.split('Гс.\s{0,}|Згс.\s{0,}|Линейные судьи\s{0,}:\s{0,}|Линейные судьи\s{0,}.\s{0,}', i) for i in areas]
        areas = [[i[j].strip().strip('\n').strip('.') for j in range(len(i))] for i in areas]
        sumjudes = []

        # На каждой из площадок получаем линейных и остальных судей
        for areaindex in range(len(areas)):
            area = areas[areaindex]
            if areaindex == 0 and len(area) == 1 and ('ГСС' in area[0] or 'ГСек' in area[0]):
                continue
                area[0] = area[0].split('\n')
                for i in range(len(area[0])):
                    area[0][i] = area[0][i].replace('ГСС. ', '')
                    area[0][i] = area[0][i].replace('ГСек.', '')
                    area[0][i] = area[0][i].strip().strip('.').strip('\n')
                otherjud = area[0]
                k = await chairman_queries.check_category_date(otherjud, user_id)
                if k != 0:
                    flag6 = 1
                    s += f'❌Ошибка: {area}: {k}\n\n'
                sumjudes.append(set(otherjud))
            else:
                linjud = re.split(',\s{0,}', area[-1])

                familylinjud = [i.split()[0] for i in linjud]
                otherjud = re.split(',\s{0,}', ', '.join(
                    [area[i] for i in range(len(area)) if i != 0 and area[i] != '' and i != len(area) - 1]))
                area = area[0]
                #group_num = re.search('Гр.\s{0,}\d+', area)
                group_num = re.search('\d+.', area[0:5].strip())
                if group_num is not None:
                    group_num = int(group_num[0].replace('.', '').strip())

                    k7 = await chairman_queries.check_min_category(otherjud, linjud, group_num, active_comp, area)
                    if k7 != 1:
                        flag7 = 1
                        s += k7

                    k2 = await chairman_queries.group_id_to_lin_const(active_comp, group_num)
                    if k2 != 0 and k2 is not None:
                        const = k2


                if '' in otherjud:
                    otherjud = []

                k = await chairman_queries.check_category_date(otherjud + linjud, user_id)
                if k != 0:
                    flag6 = 1
                    s += f'❌Ошибка: {area}: {k}\n\n'


                k1 = await chairman_queries.check_clubs_match(linjud)
                if k1 != 0:
                    s += f'❌Ошибка: {area}: Распределение линейной группы по клубам нарушает регламент\n{k1}\n'
                    flag5 = 1

                # Проверяем количество линейных
                if len(linjud) != const:
                    s += f'❌Ошибка: {area}: количество членов линейной группы не соответствует установленной норме ({const}), на площадке - {len(linjud)}\n\n'
                    flag1 = 1

                # Проверяем совмещение должностей на площадке
                if len(set(otherjud) & set(linjud)) != 0:
                    flag4 = 1
                    a = ', '.join(map(str, set(otherjud) & set(linjud)))
                    s += f'🤔{area}: {a} совмеща(ет/ют) должности внутри площадки\n\n'

                '''
                # Проверяем фамилии линейных
                if len(familylinjud) != len(set(familylinjud)):
                    s += f'❌Ошибка: {area}: внутри линейной бригады есть одинаковые фамилии\n\n'
                    flag2 = 1
                sumjudes.append(set(otherjud + linjud))
                '''
                sumjudes.append(set(otherjud + linjud))

        # Проверяем пересечения между площадками
        res = list(combinations(sumjudes, 2))
        res = [i[0] & i[1] for i in res if i[0] & i[1] != set()]
        if res != []:
            a = ', '.join(map(str, res[0]))
            s += f'❌Ошибка: {a}: работа(ет/ют) одновременно на нескольких площадках\n\n'
            flag3 = 1

        # Находим не задействованных на площадках судей
        # Находим тех, кто не бьется по judges_competition
        all_judges_areas = set()
        for i in sumjudes:
            all_judges_areas |= i

        judges_use = []

        for i in all_judges_areas:
            if len(i.split()) == 2:
                k = i.split()
                firstname = k[1]
                lastname = k[0]
            else:
                k = i.split()
                firstname = ' '.join(k[1::])
                lastname = k[0]
            for j in judges_free:
                if (j[1] == firstname and j[0] == lastname):
                    judges_use.append(j)
                    break


        config.judges_index[user_id] = judges_use
        if flag1 + flag2 + flag3 + flag4 + flag5 + flag6 + flag7 == 0:
            return (1, s)
        else:
            return (0, s)

    except Exception as e:
        print('Ошибка проверки списка судей на валидность')
        print(e)
        return (2, '')


async def get_parse(text, user_id):
    judges_problem = []
    judges_problem_db = []
    active_comp = await general_queries.get_CompId(user_id)
    conn = pymysql.connect(
        host=config.host,
        port=3306,
        user=config.user,
        password=config.password,
        database=config.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )

    areas = re.split('\n\s{0,}\n', text)
    areas = [re.split('Гс.\s{0,}|Згс.\s{0,}|Линейные судьи\s{0,}:\s{0,}|Линейные судьи\s{0,}.\s{0,}', i) for i in areas]
    areas = [[i[j].strip().strip('\n').strip('.') for j in range(len(i))] for i in areas]
    with conn:
        cur = conn.cursor()
        for areaindex in range(len(areas)):
            area = areas[areaindex]
            if areaindex == 0 and len(area) == 1 and ('ГСС' in area[0] or 'ГСек' in area[0]):
                continue
                area[0] = area[0].split('\n')
                for i in range(len(area[0])):
                    area[0][i] = area[0][i].replace('ГСС. ', '')
                    area[0][i] = area[0][i].replace('ГСек.', '')
                    area[0][i] = area[0][i].strip().strip('.').strip('\n')
                otherjud = area[0]
                linjud = []
            else:
                linjud = re.split(',\s{0,}', area[-1])
                otherjud = re.split(',\s{0,}', ', '.join(
                    [area[i] for i in range(len(area)) if i != 0 and area[i] != '' and i != len(area) - 1]))


            if '' in otherjud:
                otherjud = []
            for i in otherjud + linjud:
                if len(i.split()) == 2:
                    k = i.split()
                    firstname = k[1]
                    lastname = k[0]
                elif len(i.split()) > 2:
                    k = i.split()
                    firstname = ' '.join(k[1::])
                    lastname = k[0]

                elif len(i.split()) == 1:
                    lastname = re.search('^[А-ЯA-Z][а-яa-z]*', i)[0]
                    firstname = i.replace(lastname, '')
                    text = text.replace(lastname + firstname, lastname + ' ' + firstname)
                """
                elif len(i.split()) > 2:
                    peopls = []
                    k = i.split()
                    p = 0
                    for j in range(len(k)):
                        if p == 1:
                            p = 0
                            if k[j] != re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0]:
                                lastname = re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0].strip()
                                firstname = k[j].replace(lastname, '').strip()
                                text = text.replace(lastname + firstname, lastname + ' ' + firstname + ',')
                                peopls.append([lastname, firstname])
                            continue

                        if k[j] != re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0]:
                            lastname = re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0].strip()
                            firstname = k[j].replace(lastname, '').strip()
                            text = text.replace(lastname + firstname, lastname + ' ' + firstname + ',')
                            peopls.append([lastname, firstname])
                        else:
                            if j == len(k) - 1:
                                pass
                            else:
                                lastname, firstname = k[j], k[j + 1]
                                text = re.sub(fr'\s+{lastname}\s+{firstname}', ' ' + lastname + ' ' + firstname + ',', text)
                                peopls.append([lastname, firstname])
                                p = 1

                        if text[-1] == ',':
                            text = text[0:-1] + '.'



                        text = text.replace(',,', ',')
                        text = text.replace(',.', '')
                        text = text.replace(', .', '')
                        text = '\n\n'.join([i.strip(',') for i in re.split('\n\s{0,}\n', text)])
                        '''
                        if j == p and k[j] != re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0]:
                            lastname = re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0].strip()
                            firstname = k[j].replace(lastname, '').strip()
                            text = text.replace(lastname + firstname, lastname + ' ' + firstname)
                            peopls.append([lastname, firstname])
                        elif j == p and k[j] == re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0]:
                            pass
                        elif j != p and k[j] == re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0] and peopls[-1][1] != k[j]:
                            lastname, firstname = k[j].strip(), k[j+1].strip()
                            peopls.append([lastname, firstname])
                            if j == p - 1:
                                text = text.replace(lastname + ' ' + firstname, lastname + ' ' + firstname)
                            else:
                                text = re.sub(fr'{lastname}\s+{firstname},', lastname + ' ' + firstname + ',', text)

                        elif j != p and k[j] != re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0]:
                            lastname = re.search('^[А-ЯA-Z][а-яa-z]*', k[j])[0].strip()
                            firstname = k[j].replace(lastname, '').strip()
                            text = text.replace(lastname + firstname, lastname + ' ' + firstname + ',')
                            peopls.append([lastname, firstname])
                        '''
                    for people in peopls:
                        lastname, firstname = people
                        st1 = cur.execute(f"SELECT firstName, lastName From competition_judges WHERE (lastName = '{lastname}' OR lastName2 = '{lastname}') AND CompId = {active_comp} AND active = 1")
                        st1 = cur.fetchall()
                        if len(st1) == 1:
                            text = text.replace(lastname + ' ' + firstname, st1[0]['lastName'] + ' ' + st1[0]['firstName'])
                            continue

                        if cur.execute(
                                f"SELECT bookNumber FROM competition_judges WHERE firstName = '{firstname}' AND lastName = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:

                            if cur.execute(
                                    f"SELECT bookNumber FROM competition_judges WHERE firstName2 = '{firstname}' AND lastName2 = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:
                                judges_problem.append([lastname, firstname])
                            else:
                                judges_problem_db.append([lastname, firstname])
                else:
                    k = i.split()
                    firstname = ' '.join(k[1::])
                    lastname = k[0]
                """


                st1 = cur.execute(
                    f"SELECT firstName, lastName From competition_judges WHERE lastName2 = '{lastname}' and firstName2 = '{firstname}' AND CompId = {active_comp} AND active = 1")

                st1 = cur.fetchall()
                if len(st1) == 1:
                    text = text.replace(lastname + ' ' + firstname, st1[0]['lastName'] + ' ' + st1[0]['firstName'])
                    continue

                st1 = cur.execute( f"SELECT firstName, lastName From competition_judges WHERE lastName = '{lastname}' AND CompId = {active_comp} AND active = 1")
                st1 = cur.fetchall()
                if len(st1) == 1:
                    text = text.replace(lastname + ' ' + firstname, st1[0]['lastName'] + ' ' + st1[0]['firstName'])
                    continue

                if cur.execute(f"SELECT bookNumber FROM competition_judges WHERE firstName = '{firstname}' AND lastName = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:
                    cur.execute(f"SELECT lastName from competition_judges WHERE lastName = '{lastname}' AND active = 1")
                    ans1 = cur.fetchall()
                    cur.execute(f"SELECT lastName from competition_judges WHERE lastName2 = '{lastname}' AND active = 1")
                    ans2 = cur.fetchall()

                    if cur.execute(f"SELECT bookNumber FROM competition_judges WHERE firstName2 = '{firstname}' AND lastName2 = '{lastname}' AND compId = {active_comp} AND active = 1") == 0:
                        if [lastname, firstname] not in judges_problem:
                            judges_problem.append([lastname, firstname])
                    else:
                        if [lastname, firstname] not in judges_problem_db:
                            judges_problem_db.append([lastname, firstname])

    return judges_problem, judges_problem_db, text



async def transform_linlist(text, judges, user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        cur = conn.cursor()
        with conn:
            for jud in judges:
                if jud[-1] == 'NoneSpace':
                    lastname, firstname = jud[0:2]
                    text = text.replace(lastname + firstname, lastname + ' ' + firstname)
                else:
                    lastname, firstname = jud
                    cur.execute(f"SELECT firstName, lastName FROM competition_judges WHERE firstName2 = '{firstname}' and lastName2 = '{lastname}' and compId = {active_comp}")
                    name = cur.fetchone()
                    text = text.replace(lastname + ' ' + firstname, name['lastName'] + ' ' + name['firstName'])
            return text
    except Exception as e:
        print(e)
        return 0


async def get_all_judges(text):
    areas = re.split('\n\s{0,}\n', text)
    areas = [re.split('Гс.\s{0,}|Згс.\s{0,}|Линейные судьи\s{0,}:\s{0,}|Линейные судьи\s{0,}.\s{0,}', i) for i in areas]
    areas = [[i[j].strip().strip('\n').strip('.') for j in range(len(i))] for i in areas]
    sumjudes = []

    # На каждой из площадок получаем линейных и остальных судей
    for areaindex in range(len(areas)):
        area = areas[areaindex]
        if areaindex == 0 and len(area) == 1 and ('ГСС' in area[0] or 'ГСек' in area[0]):
            continue
            area[0] = area[0].split('\n')
            for i in range(len(area[0])):
                area[0][i] = area[0][i].replace('ГСС. ', '')
                area[0][i] = area[0][i].replace('ГСек.', '')
                area[0][i] = area[0][i].strip().strip('.').strip('\n')
            otherjud = area[0]
            sumjudes += otherjud
        else:
            linjud = re.split(',\s{0,}', area[-1])
            otherjud = re.split(',\s{0,}', ', '.join(
                [area[i] for i in range(len(area)) if i != 0 and area[i] != '' and i != len(area) - 1]))
            if '' in otherjud:
                otherjud = []
            sumjudes += linjud
            sumjudes += otherjud
    return sumjudes
