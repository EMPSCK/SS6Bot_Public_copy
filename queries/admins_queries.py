import pymysql
import config
import re
async def create_new_comp(text):
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
            text = text.split('\n')
            text = [re.split(':\s{0,}', i)[1].strip() for i in text]
            cur = conn.cursor()
            sql = "INSERT INTO competition (`date1`, `date2`, `compName`, `city`, `chairman_Id`, `scrutineerId`, `lin_const`, `isActive`, `isSecret`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, tuple(text))
            conn.commit()
            cur.close()
            return 1
    except Exception as e:
        print(e)
        print('Ошибка выполнения запроса на создание соревнования')
        return 0

async def get_tournament_list():
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
            cur.execute(f"SELECT * FROM competition")
            comp = cur.fetchall()
            cur.close()
            text = ''
            for i in comp:
                for k in i:
                    text += f'{k}: {i[k]}\n'
                text += '\n'
            return text
    except:
        print('Ошибка выполнения запроса поиск scrutineer для chairman')
        return 0

async def get_tournament(id):
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
            cur.execute(f"SELECT * FROM competition WHERE compId = {id}")
            comp = cur.fetchone()
            cur.close()
            text = ''
            for k in comp:
                if k != 'compId':
                    text += f'{k}: {comp[k]}\n'
            return text
    except:
        print('Ошибка выполнения запроса поиск scrutinner для chairman')
        return 0

async def edit_tournament(id, text):
    try:
        text = text.split('\n')
        a = [re.split(':\s{0,}', i)[1].strip() for i in text]
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
            cur.execute(f"UPDATE competition SET date1 = {a[0]}, date2 = {a[1]}, compName = '{a[2]}', city = '{a[3]}', chairman_Id = '{a[4]}', scrutineerId = '{a[5]}', lin_const = {a[6]}, isActive = {a[7]}, isSecret = {a[8]}  WHERE compId = {id}")
            conn.commit()
            cur.close()
            return 1
    except:
        print('Ошибка выполнения запроса создания соревнования')
        return 0
