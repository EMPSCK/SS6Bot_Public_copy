import config
import pymysql
import re
from queries import chairman_queries
from handlers import Chairman_menu_handler
async def load_list(tg_id, text, compid):
    try:
        flag = 0
        judges_promlem = []
        names = []


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
            judges_lst = re.split(',\s{0,}', text)
            for jud in judges_lst:
                notjud = 0
                jud = jud.strip().strip('\n').strip('.').strip()
                index = jud.split()

                if len(index) == 2:
                    last_name, name = index
                else:
                    last_name = index[0]
                    name = ' '.join(index[1::])


                # Проверяем есть ли запись в competition_judges
                if cur.execute(
                    f"SELECT firstName from competition_judges WHERE compId = {compid} and ((lastName2 = '{last_name}' and firstName2 = '{name}') OR (lastName = '{last_name}' and firstName = '{name}'))") == 1:

                    cur.execute(
                        f"UPDATE competition_judges SET active = 1 WHERE compId = {compid} and ((lastName2 = '{last_name}' and firstName2 = '{name}') OR (lastName = '{last_name}' and firstName = '{name}'))")
                    conn.commit()
                    Chairman_menu_handler.last_added_judges[tg_id].append([last_name, name])
                    continue

                notjud = re.match(r'^[a-zA-Z]+\Z', name.replace(' ', '')) is not None

                cur.execute(f"SELECT * FROM judges WHERE FirstName = '{name}' AND LastName = '{last_name}'")
                person = cur.fetchall()

                if len(person) == 0:
                    judges_promlem.append([last_name, name, 'Не обнаружена запись в бд', 2])
                    names.append(last_name+ ' ' +name)
                    continue
                elif len(person) > 1:
                    # Проверяем есть ли запись в competition_judges

                    judges_promlem.append([last_name, name, 'Невозможно однозначно определить судью', 2])
                    names.append(last_name + ' ' + name)
                    continue

                BookNumber = person[0]['BookNumber']
                SecondName = person[0]['SecondName']
                Birth = person[0]['Birth']
                DSFARR_Category = person[0]['DSFARR_Category']
                DSFARR_CategoryDate = person[0]['DSFARR_CategoryDate']
                WDSF_CategoryDate = person[0]['WDSF_CategoryDate']
                RegionId = person[0]['RegionId']
                City = person[0]['City']
                Club = person[0]['Club']
                Translit = person[0]['Translit']
                Archive = person[0]['Archive']
                SPORT_Category = person[0]['SPORT_Category']
                SPORT_CategoryDate = person[0]['SPORT_CategoryDate']
                SPORT_CategoryDateConfirm = person[0]['SPORT_CategoryDateConfirm']
                federation = person[0]['federation']
                DSFARR_Category_Id = person[0]['DSFARR_Category_Id']


                if type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) == str:
                    judges_promlem.insert(0, [last_name, name, 'На момент окончания турнира категория недействительна', 1])
                    names.append([last_name, name])
                    continue
                elif type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) != str:
                    CategoryDate = SPORT_CategoryDate
                elif type(SPORT_CategoryDateConfirm) != str and type(SPORT_CategoryDate) == str:
                    CategoryDate = SPORT_CategoryDateConfirm
                else:
                    CategoryDate = max(SPORT_CategoryDateConfirm, SPORT_CategoryDate)
                date2 = await chairman_queries.get_tournament_date(tg_id)
                a = date2 - CategoryDate
                a = a.days
                if SPORT_Category.strip() == 'Первая' or SPORT_Category.strip() == 'Вторая':
                    if a - 365 * 2 > 0:
                        judges_promlem.insert(0, [last_name, name, 'На момент окончания турнира категория недействительна', 1])
                        names.append(last_name+ ' ' +name)
                        continue

                elif SPORT_Category.strip() == 'Третья':
                    if a - 365 > 0:
                        judges_promlem.insert(0, [last_name, name, 'На момент окончания турнира категория недействительна', 1])
                        names.append(last_name+ ' '+name)
                        continue

                elif SPORT_Category.strip() == 'Всероссийская':
                    if a - 365 * 4 > 0:
                        judges_promlem.insert(0, [last_name, name, 'На момент окончания турнира категория недействительна', 1])
                        names.append(last_name+ ' '+name)
                        continue

                BookNumber = int(BookNumber)
                # Если судья уже есть в таблице competition_judges
                Chairman_menu_handler.last_added_judges[tg_id].append([last_name, name])
                if cur.execute(
                        f"SELECT id FROM competition_judges WHERE firstName = '{name}' AND lastName = '{last_name}' AND compId = {compid}") == 1:
                    cur.execute(
                        f"UPDATE competition_judges SET is_use = 0, active = 1 WHERE firstName = '{name}' AND lastName = '{last_name}' AND compId = {compid}")
                    conn.commit()
                else:
                    sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `Archive`, `bookNumber`, `notJudges`, `is_use`, `DSFARR_Category_Id`, `active`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cur.execute(sql, (
                    compid, last_name, name, SecondName, Birth, DSFARR_Category, DSFARR_CategoryDate, WDSF_CategoryDate,
                    RegionId, City, Club, Translit, SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm,
                    federation, Archive, BookNumber, notjud, 0, DSFARR_Category_Id, 1))
                    conn.commit()

            cur.close()
        if len(judges_promlem) != 0:
            return judges_promlem, names
        return 1
    except Exception as e:
        print(e)
        print(index)
        return 0
