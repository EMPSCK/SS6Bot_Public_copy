import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from queries import chairman_queries
from handlers import Chairman_comm_handler
from aiogram import types
from keyboards import chairmans_kb
from chairman_moves import check_list_judges
from queries import get_user_status_query
from queries import chairman_queries
from queries import general_queries
import re

router = Router()
current_jud_point = {}
jud_problem_list = {}
to_index_future = {}
markup_buttons = {}


async def edit_linlist(call, problem):
    problem = problem.split(':')[0]
    problem = problem[1::].split(', ')
    jud_problem_list[call.from_user.id] = problem
    markup_buttons[call.from_user.id] = await chairmans_kb.get_markup_EV(call.from_user.id, Chairman_comm_handler.linsets[call.from_user.id][0])
    len_markup_buttons = 1
    if markup_buttons == 0:
        len_markup_buttons = 0

    if len_markup_buttons == 0:
        await call.message.answer('❌Редактирование невозможно. Отсутсвует необходимое количесво свободных судей в таблице')
        return

    await edit_current_jud(call)


async def edit_current_jud(call):
    try:
        if len(jud_problem_list[call.from_user.id]) == 0:
            await call.message.delete()
            return await f2(call, Chairman_comm_handler.linsets[call.from_user.id][0])
        else:
            current_jud_point[call.from_user.id] = jud_problem_list[call.from_user.id].pop(0)


        mark = InlineKeyboardMarkup(inline_keyboard=markup_buttons[call.from_user.id])
        await call.message.edit_text(f'{current_jud_point[call.from_user.id]}\n\nВарианты замены:', reply_markup=mark)
    except Exception as e:
        print(e)
        await call.message.answer('Во время редактирования произошла ошибка, пожалуйста отправьте список еще раз')


@router.callback_query(F.data.startswith('01jud_rep_'))
async def cmd_start(call: types.CallbackQuery):
    try:
        BookNumber, lastname, firstname = call.data.replace('01jud_rep_', '').split('_')
        BookNumber = int(BookNumber)
        name = lastname + ' ' + firstname
        if len(name.split()) == 2:
            k = name.split()
            firstname1 = k[1]
            lastname1 = k[0]
        else:
            k = name.split()
            lastname1 = k[0]
            firstname1 = ' '.join(k[1::])

        name = current_jud_point[call.from_user.id]
        if len(name.split()) == 2:
            k = name.split()
            firstname2 = k[1]
            lastname2 = k[0]
        else:
            k = name.split()
            lastname2 = k[0]
            firstname2 = ' '.join(k[1::])

        #Chairman_comm_handler.linsets[call.from_user.id][0] = Chairman_comm_handler.linsets[call.from_user.id][0].replace(current_jud_point[call.from_user.id], lastname1 + ' ' + firstname1)
        q = 0

        Chairman_comm_handler.linsets[call.from_user.id][0] = re.sub(rf'{lastname2}\s+{firstname2}', lastname1 + ' ' + firstname1, Chairman_comm_handler.linsets[call.from_user.id][0])
        for row in markup_buttons[call.from_user.id]:
            for b in row:
                if b.callback_data == f'01jud_rep_{BookNumber}_{lastname}_{firstname}':
                    row.remove(b)
                    break

        await edit_current_jud(call)
    except Exception as e:
        print(e)
        await call.message.answer('Во время редактирования произошла ошибка, пожалуйста отправьте список еще раз')


@router.callback_query(F.data == 'end_edit_02')
async def cmd_start(call: types.CallbackQuery):
    try:
        Chairman_comm_handler.linsets.pop(call.from_user.id, None)
        Chairman_comm_handler.linsets.problemjudgesset_for_check_lin.pop(call.from_user.id, None)
        Chairman_comm_handler.linsets.current_problem_jud_for_check_lin.pop(call.from_user.id, None)
        current_jud_point.pop(call.from_user.id, None)
        jud_problem_list.pop(call.from_user.id, None)
        markup_buttons.pop(call.from_user.id, None)
        Chairman_comm_handler.bank_for_edit_costyl.pop(call.from_user.id, None)
    except:
        pass

    await call.message.edit_text('Редактирование Завершено')

#Копия обработчика линейных списков
async def f2(call, text):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3 or user_status == 2:
        res, msg = await check_list_judges.check_list(text, call.from_user.id)
        Chairman_comm_handler.linsets[call.from_user.id][3] = msg
        if res == 1:
            await chairman_queries.set_free_judges(call.from_user.id)
            # Перед отправкой сообщения проверяем, совпадает ли выбор турниров у пары и активно ли соревнование
            scrutineer_id = await chairman_queries.get_Scrutineer(call.from_user.id)
            if scrutineer_id == 0:
                await call.message.answer('❌Ошибка')
            else:
                active_compId_chairman = await general_queries.get_CompId(call.from_user.id)
                active_compId_scrutineer = await general_queries.get_CompId(scrutineer_id)
                is_active = await general_queries.active_or_not(active_compId_chairman)
                if is_active == 0:
                    await call.message.answer('❌Ошибка\nВыбранное соревнование неактивно')
                elif active_compId_scrutineer == active_compId_chairman:
                    try:
                        await call.message.answer(text)
                        #await chairman_queries.set_free_judges(call.from_user.id)
                        if call.from_user.username is None:
                            name = await chairman_queries.get_comment(call.from_user.id)
                        else:
                            name = f'@{call.from_user.username}'
                        await call.bot.send_message(scrutineer_id,
                                                    f"Сообщение от пользователя {name}")
                        await call.bot.send_message(scrutineer_id, text)
                        await call.message.answer('✅Информация отправлена РСК')
                    except:
                        print('Бот в бане')
                else:
                    await call.message.answer('❌Ошибка\nВыбор турниров не согласуется')
        elif res == 0:
            await chairman_queries.set_free_judges(call.from_user.id)
            await call.message.answer(text)
            await call.message.answer(msg, reply_markup=chairmans_kb.list_jud_send_kb)

        elif res == 2:
            await call.message.answer('❌Ошибка')

