import re
from aiogram import Router, F
from aiogram import types
from keyboards import chairmans_kb
from queries import chairman_queries
from queries import get_user_status_query
from queries import general_queries
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from chairman_moves import load_judges_list
import config
router = Router()
problemjudgesset = {}
current_problem_jud = {}
enter_mes = {}
confirm_tour_id = {}
last_added_judges = {}


class Load_list_judges(StatesGroup):
    next_step = State()

class Solve_judges_problem(StatesGroup):
    bookNumber = State()


#Вернуться в меню
@router.callback_query(F.data == 'back_to_chairman_menu')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        await chairman_queries.del_unactive_comp(call.from_user.id, active_comp)
        info = await general_queries.CompId_to_name(active_comp)
        await call.message.edit_text(f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\n/judges - отправить список судей\nАктивное соревнование: {info}", reply_markup = chairmans_kb.menu_kb)


#Выбрать активное соревнование
@router.callback_query(F.data == 'set_active_competition')
async def set_active_comp(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        await chairman_queries.del_unactive_comp(call.from_user.id, active_comp)
        markup = await chairmans_kb.gen_list_comp(call.from_user.id)
        info = await general_queries.CompId_to_name(active_comp)
        await call.message.edit_text(
            f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\n/judges - отправить список судей\nАктивное соревнование: {info}",
            reply_markup=markup)


#Обработка после выбора активного соревнования
@router.callback_query(F.data.startswith('comp_'))
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        compId = int(call.data.replace('comp_', ''))
        confirm_tour_id[call.from_user.id] = compId
        info = await general_queries.CompId_to_name(compId)
        await call.message.edit_text(
            f"{info}\n\nПодтвердить выбор ?",
            reply_markup=chairmans_kb.confirm_choice_kb)



@router.callback_query(F.data == 'confirm_choice')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        try:
            await chairman_queries.set_active_comp_for_chairman(call.from_user.id, confirm_tour_id[call.from_user.id])
            active_comp = await general_queries.get_CompId(call.from_user.id)
            info = await general_queries.CompId_to_name(active_comp)
            await call.message.edit_text(
                f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\n/judges - отправить список судей\nАктивное соревнование: {info}",
                reply_markup=chairmans_kb.menu_kb)
        except:
            await call.message.answer('❌Ошибка. Попробуйте еще раз через /start')


@router.callback_query(F.data == 'confirm_choice_back')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        info = await general_queries.CompId_to_name(active_comp)
        markup = await chairmans_kb.gen_list_comp(call.from_user.id)
        await call.message.edit_text(
            f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\n/judges - отправить список судей\nАктивное соревнование: {info}", reply_markup=markup)



#Очистить список судей в турнире
@router.message(Command("clean"))
async def cmd_start(message: Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        active_or_not = await general_queries.active_or_not(active_comp)
        if active_or_not == 1:
            status = await chairman_queries.cancel_load(message.from_user.id)
            if status == 1:
                await message.answer('Список очищен')
            else:
                await message.answer('❌Ошибка')
        else:
            await message.answer('❌Ошибка. Выбранное соревнование неактивно')


#Показать свободных судей
@router.message(Command("free"))
async def cmd_start(message: Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        active_or_not = await general_queries.active_or_not(active_comp)
        if active_or_not == 1:
            status = await chairman_queries.for_free(message.from_user.id)
            if status == 0:
                await message.answer('❌Ошибка')
            else:
                if len(status) > 4096:
                    for x in range(0, len(status), 4096):
                        await message.answer(status[x:x + 4096])
                else:
                    await message.answer(status)
        else:
            await message.answer('❌Ошибка. Выбранное соревнование неактивно')


#Загрузка списка судей
@router.message(Command("judges"))
async def cmd_judes(message: Message, state:FSMContext):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        last_added_judges[message.from_user.id] = []
        try:
            await state.clear()
            enter_mes.pop(message.from_user.id, None)
            current_problem_jud.pop(message.from_user.id, None)
            problemjudgesset.pop(message.from_user.id, None)
        except:
            pass

        if await chairman_queries.check_have_tour_date(message.from_user.id) == 0:
            await message.answer('❌Ошибка. Установите активный турнир')
            return

        active_compId_chairman = await general_queries.get_CompId(message.from_user.id)
        if active_compId_chairman != 0:
            is_active = await general_queries.active_or_not(active_compId_chairman)
            if is_active == 1:
                await message.answer('Отправьте список в формате: Судья№1, Судья№2, ..., Судья№n.',
                                     reply_markup=chairmans_kb.load_judges_kb)
                await state.set_state(Load_list_judges.next_step)
            else:
                await message.answer('❌Ошибка\nВыбранное соревнование неактивно')
        else:
            await message.answer('❌Ошибка\nВыберите активное соревнование')


@router.message(Load_list_judges.next_step)
async def f2(message: Message, state: FSMContext):
    compid = await general_queries.get_CompId(message.from_user.id)
    status = await load_judges_list.load_list(message.from_user.id, message.text, compid)
    if status == 1:
        status1 = await chairman_queries.check_celebrate(message.from_user.id, last_added_judges[message.from_user.id])
        if status1 != 0:
            await message.answer(status1)
        await message.answer('Список загружен')

    elif type(status) == tuple:
        problem, names = status
        a = ', '.join([i for i in names])
        problemjudgesset[message.from_user.id] = problem
        await message.answer(f'🤔{a}: требуются редактирование', reply_markup=chairmans_kb.judges_problem_kb)
    else:
        await message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')
    await state.clear()


@router.callback_query(F.data == 'cancel_load')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    try:
        enter_mes.pop(callback.from_user.id, None)
        current_problem_jud.pop(callback.from_user.id, None)
        problemjudgesset.pop(callback.from_user.id, None)
    except:
        pass
    await state.clear()
    await callback.message.delete()
    await callback.message.answer('Загрузка завершена')


@router.callback_query(F.data == 'edit_problem_judges_info')
async def edit_problem_jud(callback: types.CallbackQuery, state: FSMContext, q=1):
    await state.clear()
    try:
        problemJudges = problemjudgesset[callback.from_user.id]
        if problemJudges == [] and current_problem_jud[callback.from_user.id] == 'end':
            status1 = await chairman_queries.check_celebrate(callback.from_user.id, last_added_judges[callback.from_user.id])
            if status1 != 0:
                await callback.message.answer(status1)
            await callback.message.answer('Загрузка завершена')
            await callback.message.delete()
            return

        if q == 1:
            current_problem_jud[callback.from_user.id] = problemJudges.pop(0)

        #Не обнаружена запись в бд или невозможно однозначно определить человека
        if current_problem_jud[callback.from_user.id][3] == 2:
            name = current_problem_jud[callback.from_user.id][0] + ' ' + current_problem_jud[callback.from_user.id][1]
            p = current_problem_jud[callback.from_user.id][2]
            await callback.message.edit_text(f"{name}\n{p}\n\nВыберите действие:", reply_markup=chairmans_kb.choose_problem_jud_action_kb)

        #На момент окончания турнира категория недействительна
        elif current_problem_jud[callback.from_user.id][3] == 1:
            name = current_problem_jud[callback.from_user.id][0] + ' ' + current_problem_jud[callback.from_user.id][1]
            p = current_problem_jud[callback.from_user.id][2]
            await callback.message.edit_text(f"{name}\n{p}\n\nВыберите действие:",reply_markup=chairmans_kb.choose_problem_jud_action_kb_1)

    except Exception as e:
        print(e)
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


async def edit_problem_jud_after_enter_booknum(message: Message, state: FSMContext, q=1):
    await state.clear()
    try:
        problemJudges = problemjudgesset[message.from_user.id]
        if problemJudges == [] and current_problem_jud[message.from_user.id] == 'end':
            status1 = await chairman_queries.check_celebrate(message.from_user.id, last_added_judges[message.from_user.id])
            if status1 != 0:
                await message.answer(status1)
            await message.answer('Загрузка завершена')
            return
        if q == 1:
            current_problem_jud[message.from_user.id] = problemJudges.pop(0)

        if current_problem_jud[message.from_user.id][3] == 2:
            name = current_problem_jud[message.from_user.id][0] + ' ' + current_problem_jud[message.from_user.id][1]
            p = current_problem_jud[message.from_user.id][2]
            await message.answer(f"{name}\n{p}\n\nВыберите действие:", reply_markup=chairmans_kb.choose_problem_jud_action_kb)
        elif current_problem_jud[message.from_user.id][3] == 1:
            name = current_problem_jud[message.from_user.id][0] + ' ' + current_problem_jud[message.from_user.id][1]
            p = current_problem_jud[message.from_user.id][2]
            await message.answer(f"{name}\n{p}\n\nВыберите действие:",reply_markup=chairmans_kb.choose_problem_jud_action_kb_1)

    except Exception as e:
        print(e)
        await message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


#Отправить как есть судью которого не смогли пробить по бд
@router.callback_query(F.data == 'take_as_is')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    try:
        jud = current_problem_jud[callback.from_user.id]

        await chairman_queries.set_problem_jud_as_is(callback.from_user.id, jud[0] + ' ' +jud[1])

        if problemjudgesset[callback.from_user.id] == []:
            current_problem_jud[callback.from_user.id] = 'end'

        await edit_problem_jud(callback, state, 1)
    except:
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')

#Отправить как есть судью с проблемой по категории
@router.callback_query(F.data == 'take_as_is_1')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    try:
        jud = current_problem_jud[callback.from_user.id]
        name = ''
        if len(jud) > 4:
            name = jud[4]
        await chairman_queries.set_problem_jud_as_is_1(callback.from_user.id, jud[0] + ' ' +jud[1], name)
        if problemjudgesset[callback.from_user.id] == []:
            current_problem_jud[callback.from_user.id] = 'end'

        await edit_problem_jud(callback, state, 1)
    except:
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


#Пропустить судью в загрузке списка
@router.callback_query(F.data == 'do_gap')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    if problemjudgesset[callback.from_user.id] == []:
        current_problem_jud[callback.from_user.id] = 'end'
    await edit_problem_jud(callback, state, 1)

@router.callback_query(F.data == 'enter_book_number')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    enter_mes[callback.from_user.id] = callback.message.message_id
    try:
        jud = current_problem_jud[callback.from_user.id]
        await callback.message.edit_text(f"{jud[0] + ' ' +jud[1]}\n\nВведите номер книжки:", reply_markup=chairmans_kb.book_number_kb)
        await state.set_state(Solve_judges_problem.bookNumber)
    except:
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


@router.message(Solve_judges_problem.bookNumber)
async def f2(message: Message, state: FSMContext):
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=enter_mes[message.from_user.id])
        await message.delete()
        booknumber = message.text
        jud = current_problem_jud[message.from_user.id]
        status = await chairman_queries.check_cat_for_enter_book_number(message.from_user.id, int(booknumber))
        if status == 1:
            await chairman_queries.set_problem_jud_as_is(message.from_user.id, jud[0] + ' ' +jud[1], booknumber)
            if problemjudgesset[message.from_user.id] == []:
                current_problem_jud[message.from_user.id] = 'end'

            await edit_problem_jud_after_enter_booknum(message, state, 1)
            await state.clear()
        else:
            last, first = await chairman_queries.booknumber_to_name_1(int(booknumber))
            problemjudgesset[message.from_user.id].insert(0, [last, first, 'На момент окончания турнира категория недействительна', 1, jud[0] + ' ' + jud[1] + '|' + str(booknumber)])
            await edit_problem_jud_after_enter_booknum(message, state, 1)
            await state.clear()


    except Exception as e:
        await state.clear()
        print(e)
        await message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


@router.callback_query(F.data == 'search_for_db')
async def f2(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        jud = current_problem_jud[callback.from_user.id]
        mark = await chairmans_kb.gen_similar_judges(jud[0] + ' ' +jud[1])
        await callback.message.edit_text(f"{jud[0] + ' ' +jud[1]}\nВозможные варианты:",
                             reply_markup=mark)
    except Exception as e:
        await state.clear()
        print(e)
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')



@router.callback_query(F.data == 'back_to_edit_jud')
async def f2(callback: types.CallbackQuery, state: FSMContext):
    await edit_problem_jud(callback, state, 0)


@router.callback_query(F.data.startswith('jud_'))
async def cmd_start(call: types.CallbackQuery, state: FSMContext):
    try:
        BookNumber = int(call.data.replace('jud_', ''))
        name = call.message.text.replace('Возможные варианты:', '').strip().strip('\n').strip() + f'|{BookNumber}'
        status = await chairman_queries.check_category_date_for_book_id(BookNumber, call.from_user.id)
        if status == 1:
            await chairman_queries.add_problemcorrect_jud(BookNumber, call.from_user.id, name.split('|')[0])

            if problemjudgesset[call.from_user.id] == []:
                current_problem_jud[call.from_user.id] = 'end'

            await edit_problem_jud(call, state)
        else:
            lastname, firstname = await chairman_queries.BookNumber_to_name(BookNumber)
            problemjudgesset[call.from_user.id].insert(0, [lastname, firstname, 'На момент окончания турнира категория недействительна', 1, name])
            await edit_problem_jud(call, state, 1)
    except:
        await state.clear()
        await call.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')

