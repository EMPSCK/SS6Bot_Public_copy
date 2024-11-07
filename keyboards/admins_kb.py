from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


cancel_button = [InlineKeyboardButton(text="Отменить операцию", callback_data='cancel_load')]
load_judges_kb = InlineKeyboardMarkup(inline_keyboard=[cancel_button])

menu_button_1 = [InlineKeyboardButton(text='Создать турнир', callback_data='create_competition')]
menu_button_2 = [InlineKeyboardButton(text='Редактировать турнир', callback_data='edit_competition')]
menu_button_3 = [InlineKeyboardButton(text='Вывести список турниров', callback_data='show_tournament_list')]
menu_button_4 = [InlineKeyboardButton(text='Обновить базу судей ФТСАРР', callback_data='update_fttsar_judges')]
menu_kb = InlineKeyboardMarkup(inline_keyboard=[menu_button_1, menu_button_3, menu_button_2, menu_button_4])


create_comp_button_2 = [InlineKeyboardButton(text='Вернуться к меню', callback_data='cancel_create_comp')]
create_comp_kb = InlineKeyboardMarkup(inline_keyboard=[create_comp_button_2])
