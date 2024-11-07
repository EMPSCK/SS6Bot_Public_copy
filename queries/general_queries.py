import config
import pymysql

async def active_or_not(id):
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
            cur.execute(f"SELECT isActive FROM competition WHERE compId = {id}")
            active_or_not1 = cur.fetchone()
            cur.close()
            ans = active_or_not1['isActive']
            return ans
    except:
        print('Ошибка выполнения запроса активное соревнование или нет')
        return 0


async def get_CompId(tg_id):
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
            cur.execute(f"SELECT id_active_comp FROM skatebotusers WHERE tg_id = {tg_id}")
            id_active_comp = cur.fetchone()
            cur.close()
            return id_active_comp['id_active_comp']
    except Exception as e:
        print('Ошибка выполнения запроса поиск активного соревнования')
        return 0

async def CompId_to_name(id):
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
            cur.execute(f"SELECT compName, date1, date2, city FROM competition WHERE compId = {id}")
            name = cur.fetchone()
            cur.close()
            if name == None:
                return 'не установлено'
            return f"{name['compName']}\n{str(name['date1'])};{str(name['date2'])}|{name['city']}"

    except Exception as e:
        print(e)
        print('Ошибка выполнения запроса поиск активного соревнования')
        return 'не установлено'


async def get_tournament_lin_const(compId):
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
            cur.execute(f"SELECT lin_const FROM competition WHERE compId = {compId}")
            name = cur.fetchone()
            cur.close()
            return name['lin_const']
    except:
        print('Ошибка выполнения запроса поиск const соревнования')
        return 0


async def get_judges_free(compId):
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
            cur.execute(f"SELECT * FROM competition_judges WHERE compId = {compId} AND is_use = 0")
            name = cur.fetchall()
            cur.close()
            return name
    except:
        print('Ошибка выполнения запроса поиск свободных судей')
        return 0