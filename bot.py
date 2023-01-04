import time
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

TOKEN = '5630269099:AAGYTYb8FCm_7e1nGGG6_v83FHlrUug87yU'

storage: MemoryStorage = MemoryStorage()

bot = Bot(token = TOKEN)
dp = Dispatcher(bot = bot, storage = storage)

class MessageInfo(StatesGroup): #состояние данных пользователя
    fill_name = State()
    fill_message = State()
    fill_photo = State()
    fill_mail = State()

async def set_main_menu(dp: Dispatcher):
    main_menu_commands = [
        types.BotCommand(command='/start', description='Начало'),
        types.BotCommand(command='/help', description='Помощь')
    ]
    await dp.bot.set_my_commands(main_menu_commands)

@dp.message_handler(commands = ['start']) #функция старта
async def send_start_message(message: types.Message):
    print(message)
    name = message.from_user.first_name
    user_id = message.from_user.id
    await bot.send_message(user_id, f'Привет, <u>{name}</u>',parse_mode='html')
    keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_1: InlineKeyboardButton = InlineKeyboardButton(text="Поехали", callback_data = 'first_step')
    keyboard.add(button_1)
    await bot.send_message(user_id, 'Я умею отправлять сообщения на почту, начнем?', reply_markup=keyboard)

@dp.callback_query_handler() #хэндлер, переводящий в состояние ожидания имени
async def get_user_name(callback: types.CallbackQuery):
    match callback.data: 
        case 'first_step':
            await callback.message.edit_text(text = 'Напиши имя отправителя')
            await MessageInfo.fill_name.set()
        case 'photo_no':  #добавить config с строками
            await callback.message.edit_text(text = 'Сообщение отправлено, приходи еще ♥')
        case 'photo_yes':
            await callback.message.edit_text(text = 'Отправь мне фотографию')
            await MessageInfo.fill_photo.set()

@dp.message_handler(state = MessageInfo.fill_name) #получение и обработка имени
async def get_user_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer(text='Спасибо!\n\nА теперь введи текст')
    await MessageInfo.fill_message.set()

@dp.message_handler(state = MessageInfo.fill_message) #получение и обработка текста
async def get_user_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text
    await message.answer(text='Супер!\n\nОтправляй почту')
    await MessageInfo.fill_mail.set()

@dp.message_handler(state = MessageInfo.fill_mail) #получение и обработка почты
async def get_user_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['mail'] = message.text
    await state.finish()
    skeyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    sbutton_1: InlineKeyboardButton = InlineKeyboardButton(text="Да", callback_data = 'photo_yes')
    sbutton_2: InlineKeyboardButton = InlineKeyboardButton(text="Нет", callback_data = 'photo_no')
    skeyboard.add(sbutton_1, sbutton_2)
    await message.answer(text='Сделано!\n\nНужно ли отправить фотографию?', reply_markup=skeyboard)

# @dp.callback_query_handler() #узнать, есть ли фото в сообщении  ПОКА НЕ НУЖНО (МОЖЕТ И ИЗНАЧАЛЬНО НЕ НУЖНО БЫЛО)
# async def with_photo_callback(callback: types.CallbackQuery):
#     if callback.data == 'with_photo':
#         await callback.message.edit_text(text = 'Напиши имя отправителя')
#         await MessageInfo.fill_message.set()
        # await bot.send_message(callback.from_user.id, 'Ты выбрал сообщение с фото') это прислать новое сообщение, пусть будет на всякий 
        # await bot.send_message(callback.from_user.id, 'Пришли текст своего сообщения') 
    # else:
    #     await callback.message.edit_text(text = 'Пришли текст своего сообщения')

@dp.message_handler(commands = ['help']) #функция для хелпа (пока хз зачем)
async def send_help_message(message: types.Message):
    print(message)   
    name = message.from_user.first_name
    user_id = message.from_user.id
    await bot.send_message(user_id, message)

@dp.message_handler(content_types = ['photo'], state = MessageInfo.fill_photo) #функция дли обработки фоток
async def get_user_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[2].file_id
    try:
        file = await bot.get_file(photo_id)
        file_path = file.file_path
        await bot.download_file(file_path, 'photo.jpg')
        photo = open('photo.jpg', 'rb')
        #await bot.send_photo(user_id, photo) для теста, получается ли фотка нормально
        await bot.send_message(user_id, 'Фото получено, сообщение отправлено')
        await state.finish()
    except Exception as error:
        print(str(error))

@dp.message_handler(content_types = ['text'])
async def get_text(message: types.Message):
    text = message.text
    print(text)
    await bot.send_message(message.from_user.id, 'Выбери команду, которая тебе нужна')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=set_main_menu)