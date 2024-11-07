import random
import json
import config
import pymysql
import asyncio
data = {
    "compId": 6,
    "regionId": 78,
    "status": 12,
    "groupList": [29]
}

async def get_ans(data):
    json_end = dict()
    json_export = dict()
    group_list = []

    group_list_raw = data['groupList']
    for group_id_inp in group_list_raw:
        r = await get_group_params(data['compId'], group_id_inp)
        #Не нашли группу
        if r == "undefinedGroup":
            json_end['group_number'] = group_id_inp
            json_end['status'] = "fail"
            json_end['msg'] = 'Группа не была обнаружена'
            json_end['judge_id'] = []
            json_export[group_id_inp] = json_end
        else:
            group_list.append(r)

    #Все группы не пробились
    if group_list == []:
        ans = await json_to_message(json_export, data)
        return ans

    judge_counter_list = await get_future_tables()
    relatives_list = await get_relative_list(data['compId'])
    black_list = await get_black_list(data['compId'])


    comp_region_id = data['regionId']
    relatives_dict = await relatives_list_change(relatives_list)

    # 1. сортировка входящего списка групп в зависимости от требуемой для судейства категории
    group_list.sort(key=lambda x: x[2] * -1)

    # 2. запрашиваем и обрабатываем список судей
    ans = await get_all_judges_yana(data['compId'])
    #print(relatives_list)
    #print(black_list)
    #print()
    #for i in ans:
    #    print(i)

    all_judges_list = {}  # преобразуем словарь для более удобной работы, создаем общий список доступных для выбора судей с параметрами

    for i in ans:
        i['SPORT_Category_decoded'] = await decode_category(i['SPORT_Category'])
        all_judges_list[i['id']] = i

    s = 0

    # 3. начинаем работать с каждой группой из переданного списка
    for i in group_list:
        json_end = dict()

        s += 1
        if s == 0: sucess_result = 0

        """
        Если нам передали несколько групп, то есть мы должны генерить в параллель
        и если это уже не первая группа и предыдущая была сгенерена успешно
        тогда из общего списка судей выкидываем всех кого нагенерили в панельки ранее
        """
        if s > 1 and sucess_result == 1:
            group_all_judges_list = all_judges_list.copy()
            for j in group_finish_judges_list:
                group_all_judges_list.pop(j, None)
            group_finish_judges_list = []
            regions = {}
            sucess_result = 0
        else:
            group_all_judges_list = all_judges_list.copy()  # общий список судей из которого будем случайно выбирать
            group_finish_judges_list = []  # список, в котором финально будем передавать судей, оценивающих категорию
            regions = {}  # счетчик судейств по регионам

        # определяем параметры группы
        n_judges, min_category = i[1], i[2]
        if min_category is None: min_category = 0
        #otd_num = group_list[i]['otd_num']

        group_number = i[0]
        n_judges_category = 0

        # определяем условия на регионы судей
        n_jud_comp_region, n_jud_other_region = await rc_a_region_rules(comp_region_id, n_judges)

        group_all_judges_list = await judges_category_filter(group_all_judges_list,
                                                       min_category)  # 4. удаляем судей с неподходящей категорией

        black_list_cat = await black_list_convert(group_number,
                                            black_list)  # 5. определяем судей с запретом на судейство в конкретной категории
        group_all_judges_list = await judges_black_list_filter(group_all_judges_list,
                                                         black_list_cat)  # 6. удаляем таких судей из категории


        if len(group_all_judges_list) >= n_judges:
            while n_judges_category < n_judges:
                if len(group_all_judges_list) > 0:
                    # после чисток выбираем рандомного судью из списка
                    try_judge_data = await get_random_judge(group_all_judges_list)

                    # обновляем данные о судейском составе текущей группы
                    group_finish_judges_list.append(try_judge_data['id'])  # добавили судью в список выбранных
                    n_judges_category += 1  # количество набранных судей в категорию увеличилось на 1

                    # добавили информацию о регионе судьи в словарь по регионам
                    if try_judge_data['RegionId'] in regions:
                        regions[try_judge_data['RegionId']] += 1
                        if try_judge_data['RegionId'] == comp_region_id and regions[try_judge_data[
                            'RegionId']] == n_jud_comp_region:  # если судья из "домашнего" региона и при его добавлении лимит для региона исчерпан
                            # ФУНКЦИЯ удаляем всех судей с таким же регионом
                            group_all_judges_list = await delete_region_from_judges(group_all_judges_list,
                                                                              try_judge_data['RegionId'])
                        elif try_judge_data['RegionId'] != comp_region_id and regions[
                            try_judge_data['RegionId']] == n_jud_other_region:
                            # ФУНКЦИЯ удаляем всех судей с таким же регионом
                            group_all_judges_list = await delete_region_from_judges(group_all_judges_list,
                                                                              try_judge_data['RegionId'])
                    else:
                        regions[try_judge_data['RegionId']] = 1

                    # удалили всех с таким же клубом
                    group_all_judges_list = await delete_club_from_judges(group_all_judges_list, try_judge_data['Club'])

                    # обновляем данные о судях, доступных для выбора
                    group_all_judges_list.pop(try_judge_data['id'],
                                              None)  # судью которого мы выбрали второй раз выбрать нельзя
                    # если у судьи есть родственники, то применяем функцию для удаления родственников
                    if try_judge_data['id'] in relatives_dict:
                        for i in relatives_dict[try_judge_data['id']]:
                            group_all_judges_list.pop(i, None)

                    if n_judges_category == n_judges:  # если набрали необходимое количество судей, то успех
                        sucess_result = 1
                else:
                    sucess_result = 0
                    json_end['group_number'] = group_number
                    json_end['status'] = "fail"
                    json_end['msg'] = 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте сгенерирвать еще раз или уменьшить количество судей в бригаде.'
                    break
            else:
                json_end['group_number'] = group_number
                json_end['status'] = "success"
                json_end['judge_id'] = list()
                for i in group_finish_judges_list:
                    json_end['judge_id'].append(all_judges_list[i]['id'])
        else:
            sucess_result = 0
            json_end['group_number'] = group_number
            json_end['status'] = "fail"
            json_end['msg'] = 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте сгенерирвать еще раз или уменьшить количество судей в бригаде'

        json_export[group_number] = json_end

    #json.loads(json.dumps(json_export))
    ans = await json_to_message(json_export, data)
    #print(regions)
    return ans


#получить параметр групп по турниру и номеру
async def get_group_params(comp_id, group_id):
    try:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            cur.execute(
                f'''SELECT groupNumber,judges, minCategoryId
                 from competition_group
                 WHERE compId = {comp_id} and groupNumber = {group_id}
                                        ''')
            data = cur.fetchone()
            if data is None:
                return "undefinedGroup"
            else:
                if data['judges'] is None:
                    data['judges'] = 0
                if data['minCategoryId'] is None:
                    data['minCategoryId'] = 0

                return data['groupNumber'], data['judges'], data['minCategoryId']
    except:
        return 0

#функция для ограничения на регионы
async def rc_a_region_rules(comp_region_id, n_judges):
  if n_judges == 7:
    return(3, 2)
  elif n_judges == 9:
    return(4, 2)
  elif n_judges == 11:
    return(5, 3)
  elif n_judges == 13:
    return(6, 3)


#костыль пока не таблиц в БД
async def get_future_tables():
    #group_list = {
        #21: {'name': 'Мужчины и женщины латиноамериканская программа', 'min_category': 8, 'otd_num': 11,
    #     'n_judges': 11},
        #22: {'name': 'Мужчины и женщины европейская программа', 'min_category': 7, 'otd_num': 11, 'n_judges': 9},
        # 23: {'name': 'Мужчины и женщины двоеборье', 'min_category': 5, 'otd_num' : 11, 'n_judges': 9},
        # 24: {'name': 'Мужчины и женщины сальса', 'min_category': 7, 'otd_num' : 11, 'n_judges': 9}
    #}

    '''
    relatives_list = [
        {'id': 1,
         'relative_id': 3},
        {'id': 3,
         'relative_id': 1}
    ]
    '''
    '''
    black_list = [
        {'group_number': 21,
         'id': 1},
        {'group_number': 21,
         'id': 5},
        {'group_number': 21,
         'id': 67}
    ]
    '''

    judge_counter_list = [{'otd_num': 11, 'id': i, 'jud_entries': 0} for i in range(1, 101)]
    return judge_counter_list


async def get_relative_list(compId):
    try:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            ans = []
            cur.execute(f"select firstId, secondId from judges_relatives where compId = {compId}")
            data = cur.fetchall()
            for connect in data:
                ans.append({'id': connect["firstId"], 'relative_id': connect["secondId"]})

            return ans

    except Exception as e:
        print(e, 'get_relative_list')


async def get_black_list(compId):
    try:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            ans = []
            cur.execute(f"select judgeId, groupNumber from competition_group_interdiction where compId = {compId}")
            data = cur.fetchall()
            for interdiction in data:
                ans.append({'group_number': interdiction['groupNumber'], 'id': interdiction['judgeId']})

            return ans

    except Exception as e:
        print(e, 'get_black_list')

async def get_all_judges_yana(compId):
    try:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            cur.execute(
               f"SELECT id, lastName, firstName, SPORT_Category, RegionId, Club, bookNumber FROM competition_judges WHERE compId = {compId} and active = 1")  # выбираем только активных на данный момент судей
            data = cur.fetchall()
            return data

    except Exception as e:
        print(e)
        return 0

#преобразование категории судьи
async def decode_category(category_name):

    judge_category = {
        'Всероссийская' :6,
        'Первая' : 5,
        'Вторая' : 4,
        'Третья' : 3,
        'Четвертая': 2
    }

    try:
        category_num = judge_category[category_name]
    except KeyError:
        return 10
    return category_num

#функция удаляет судей с категорией ниже минимальной для группы
async def judges_category_filter(all_judges_list, min_category):
    all_judges_list_1 = all_judges_list.copy()
    for i in all_judges_list:
        if all_judges_list_1[i]['SPORT_Category_decoded'] < min_category:
            all_judges_list_1.pop(i, None)
    return all_judges_list_1

#функция предварительной обработки блэклиста - по номеру категории определяем судей с запретом, на выход - айдишники судей
async def black_list_convert(category_number, black_list):
  category_black_list = []
  for i in black_list:
    if i['group_number'] == category_number:
      category_black_list.append(i['id'])
  return category_black_list

#функция удаляет судей с запретом на судейство в категории
async def judges_black_list_filter(all_judges_list, category_black_list):
  all_judges_list_1 = all_judges_list.copy()
  for i in all_judges_list:
    if i in category_black_list:
      all_judges_list_1.pop(i, None)
  return all_judges_list_1

#функция генерирует случайного судью
async def get_random_judge(group_all_judges_list):
  random_number = random.randint(0, len(group_all_judges_list.keys()) - 1) #генерация случайного индекса
  return group_all_judges_list[list(group_all_judges_list.keys())[random_number]] #достаем из общего списка судей параметры по судье исходя из случайного индекса

#функция удаляет всех судей с таким же клубом
async def delete_club_from_judges(list_of_judges, club_name):
  dict_for_pop = list_of_judges.copy()
  for i in list(list_of_judges.values()):
    if i['Club'] == club_name:
      dict_for_pop.pop(i['id'], None)
  return dict_for_pop


#функция удаляет всех судей с таким же регионом
async def delete_region_from_judges(list_of_judges, region_id):

  dict_for_pop = list_of_judges.copy()
  for i in list(list_of_judges.values()):
    if i['RegionId'] == region_id:
      dict_for_pop.pop(i['id'], None)
  return dict_for_pop


# преобразование списка родственников после загрузки
async def relatives_list_change(relatives_list):

    relatives_dict = {}
    for i in relatives_list:
        if i['id'] in relatives_dict:
            relatives_dict[i['id']].append(i['relative_id'])
        else:
            relatives_dict[i['id']] = list()
            relatives_dict[i['id']].append(i['relative_id'])

    return relatives_dict


async def ids_to_names(judges, active_comp):
    conn = pymysql.connect(
        host=config.host,
        port=3306,
        user=config.user,
        password=config.password,
        database=config.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    with conn:
        cur = conn.cursor()
        r = []
        for judid in judges:
            cur.execute(f"select lastName, firstName from competition_judges where compId = {active_comp} and id = {judid} and active = 1")
            ans = cur.fetchone()
            r.append(f'{ans["lastName"]} {ans["firstName"]}')
        return ', '.join(r)


async def json_to_message(json_export, data):
    r = []
    for key in json_export:
        if json_export[key]['status'] == 'success':
            peoples = await ids_to_names(json_export[key]['judge_id'], data['compId'])
            text = f'{key}\nЛинейные судьи: {peoples}'
            r.append(text)

        if json_export[key]['status'] == 'fail':
            text = f'{key}\nЛинейные судьи: {json_export[key]["msg"]}'
            r.append(text)
    return '\n\n'.join(r)

loop = asyncio.get_event_loop()
ans = loop.run_until_complete(get_ans(data))
loop.close()
print(ans)
