import pymysql
import config
import asyncio
import os
import requests
from config import updatetime
async def compid_to_chairman(compid):
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
            cur.execute(f"SELECT chairman_Id from competition where compid = {compid}")
            ans = cur.fetchone()
            return ans['chairman_Id']
    except:
        return 0

from aiogram.types import FSInputFile
async def filesmanager(bot):
    while True:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            # Чистим таблицу со старыми копиями, заполняем ее новыми
            cur = conn.cursor()
            cur.execute("DELETE FROM competition_files_copy")
            conn.commit()
            cur.execute("INSERT INTO competition_files_copy SELECT * FROM competition_files")
            conn.commit()
            cur.execute("SELECT * FROM competition_files")
            ans = cur.fetchall()
            for file in ans:
                url = file['loadUrl']
                compid = file['compId']
                delurl = file['deleteUrl']
                groupName = file['groupName']
                groupNumber = file['groupId']
                turName = file['turName']
                fileTitle = file['fileTitle']
                fileName = file['fileName']
                chairman_id = await compid_to_chairman(compid)

                response = requests.get(url)
                if response.status_code == 200:
                    file = open(fileName, 'wb')
                    file.write(response.content)
                    file.close()
                    text = str(groupNumber) + '_' + groupName + ', ' + turName + '. ' + fileTitle
                    print(text, fileName)
                    await bot.send_document(chat_id=chairman_id, document=FSInputFile(fileName), caption=text)
                    print(1)
                    os.remove(fileName)
                    response = requests.get(delurl)
            cur.execute(f"DELETE FROM competition_files")
            conn.commit()
        await asyncio.sleep(updatetime)
