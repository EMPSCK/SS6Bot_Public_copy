from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import types
import config
from queries import get_user_status_query
from queries import general_queries
from keyboards import chairmans_kb
from keyboards import scrutineer_kb
from keyboards import admins_kb
from queries import chairman_queries
from aiogram.fsm.context import FSMContext
from admin_moves import update_fttsar_judges
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    #Админ
    if user_status == 1:
        await message.answer('👋Добро пожаловать в admin интерфейс бота SS6', reply_markup=admins_kb.menu_kb)

    #scrutinner
    if user_status == 2:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        await chairman_queries.del_unactive_comp(message.from_user.id, active_comp)
        info = await general_queries.CompId_to_name(active_comp)
        await message.answer(f"👋Добро пожаловать в scrutineer интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}", reply_markup=scrutineer_kb.menu_kb)

    #chairman
    if user_status == 3:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        await chairman_queries.del_unactive_comp(message.from_user.id, active_comp)
        info = await general_queries.CompId_to_name(active_comp)
        await message.answer(f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/judges - отправить список судей\n/help - список всех команд\nАктивное соревнование: {info}", reply_markup = chairmans_kb.menu_kb)

    if user_status == 0:
        await message.answer("👋Добро пожаловать в интерфейс бота SS6\n\nДля начала работы необходимо пройти регистрацию в системе", reply_markup=chairmans_kb.send_id_to_admin_kb)


@router.callback_query(F.data == 'send_id_to_admin')
async def cmd_start(callback: types.CallbackQuery):
    if callback.from_user.username is None:
        await callback.message.bot.send_message(config.ADMIN_ID, f'@{callback.from_user.first_name} {callback.from_user.last_name}: {callback.from_user.id}')
    else:
        await callback.message.bot.send_message(config.ADMIN_ID, f'@{callback.from_user.username}: {callback.from_user.id}')
    await callback.message.edit_text("✅Данные отправлены", reply_markup=chairmans_kb.update_status_kb)


@router.callback_query(F.data == 'update_status')
async def cmd_start(callback: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(callback.from_user.id)
    active_comp = await general_queries.get_CompId(callback.from_user.id)
    info = await general_queries.CompId_to_name(active_comp)
    if user_status == 1:
        user_status = 'admin'
    elif user_status == 2:
        user_status = 'scrutineer'
    elif user_status == 3:
        user_status = 'chairman'
    else:
        user_status = 'не определен'

    if user_status != 'не определен':
        if user_status == 'admin':
            await callback.message.edit_text('👋Добро пожаловать в admin интерфейс бота SS6',
                                             reply_markup=admins_kb.menu_kb)

        # scrutinner
        if user_status == 'scrutineer':
            active_comp = await general_queries.get_CompId(callback.from_user.id)
            info = await general_queries.CompId_to_name(active_comp)
            await callback.message.edit_text(
                f"👋Добро пожаловать в scrutineer интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}",
                reply_markup=scrutineer_kb.menu_kb)

        # chairman
        if user_status == 'chairman':
            active_comp = await general_queries.get_CompId(callback.from_user.id)
            info = await general_queries.CompId_to_name(active_comp)
            await callback.message.edit_text(
                f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/judges - отправить список судей\n/help - список всех команд\nАктивное соревнование: {info}",
                reply_markup=chairmans_kb.menu_kb)

    else:
        await callback.message.edit_text(
            f"🗓Статус: {user_status}\nАктивное соревнование: {info}\nИзменений не обнаружено",
            reply_markup=chairmans_kb.update_status_kb)




@router.message(Command("updateftsarrlist"))
async def update_ftsarr_judges_list(message: types.Message):
    access = [6887839538, 834140698, 363846616, 5824158064]
    if message.from_user.id in access:
        await message.answer('Запущен процесс обновления данных\nПримерное время ожидания: 5 мин.')
        status = await update_fttsar_judges.update_judges_list()
        if status == 1:
            await message.answer('Процесс обновления данных завершен')
        else:
            await message.answer('❌Ошибка')


@router.message(Command("help"))
async def update_ftsarr_judges_list(message: types.Message):
    text = '''<b>Список команд:</b>\n/judges - начать загрузку списка судей, chairman/scrutineer\n\n/clean - удалить загруженных внутри соревнования, chairman/scrutineer\n\n/free - показать свободных после отправки последнего списка, chairman/scrutineer\n\n/updateftsarrlist - обновить общий список судей, Митя1/Митя2/Артем1/Артем2\n\n/delactive - снести активность всем судьям внутри соревнования, chairman/scrutineer'''
    await message.answer(text, parse_mode='HTML')