import pymysql
import config


async def get_user_status(tg_id):
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
            cur.execute(f"SELECT status FROM skatebotusers WHERE tg_id = {tg_id}")
            status = cur.fetchone()
            cur.close()
            return status['status']
    except:
        print('Ошибка выполнения запроса на поиск статуса')
        return 0
