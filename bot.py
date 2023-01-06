import re

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

import mail_checking

TOKEN = '5630269099:AAGYTYb8FCm_7e1nGGG6_v83FHlrUug87yU'

storage: MemoryStorage = MemoryStorage()

bot = Bot(token = TOKEN)
dp = Dispatcher(bot = bot, storage = storage)

class MessageInfo(StatesGroup): #состояние данных пользователя
    fill_name = State()
    fill_message = State()
    fill_photo = State()
    fill_mail = State()

regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
def isValid(email):
    if re.fullmatch(regex, email):
      return True
    else:
      return False

async def set_main_menu(dp: Dispatcher):
    main_menu_commands = [
        types.BotCommand(command ='/send', description = 'Вернуться в начало'),
        types.BotCommand(command ='/help', description = 'Помощь'),
        types.BotCommand(command = '/cancel', description = 'Отменить заполнение' )
    ]
    await dp.bot.set_my_commands(main_menu_commands)

@dp.message_handler(commands = ['start']) #приветствие пользователя
async def send_start_message(message: types.Message):
    name = message.from_user.first_name
    user_id = message.from_user.id
    await bot.send_message(user_id, f'Привет, {name}\n\nЧтобы начать работу, введи /send')

@dp.message_handler(commands = ['cancel'], state = '*')
async def cancel_command(message: types.Message, state: FSMContext):
    await message.answer(text = 'Ты вышел из отправки сообщений\n\nЧтобы заново заполнить форму, введи  /send')
    await state.reset_state()

@dp.message_handler(commands = ['send']) #начало заполнения анкеты
async def form_start(message: types.Message):
    keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_1: InlineKeyboardButton = InlineKeyboardButton(text="Поехали", callback_data = 'first_step')
    keyboard.add(button_1)
    await message.answer(text = 'Я умею отправлять сообщения на почту, начнем?', reply_markup=keyboard)

@dp.callback_query_handler(state = '*') #хэндлер коллбеков
async def get_callback(callback: types.CallbackQuery):
    match callback.data:
        case 'first_step':
            await callback.message.edit_text(text = 'Напиши имя отправителя')
            await MessageInfo.fill_name.set()
        case 'photo_no':  #добавить config с строками
            await callback.message.edit_text(text = 'Сообщение отправлено, чтобы вернуться в начало, введи /send')
        case 'photo_yes':
            await callback.message.edit_text(text = 'Отправь мне фотографию')
            await MessageInfo.fill_photo.set()
        case 'go_back_to_text':
            await callback.message.edit_text(text = 'text')


@dp.message_handler(lambda message: message.text.isalpha() and len(message.text)>1, state = MessageInfo.fill_name) #получение и обработка имени
async def get_user_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer(text='Приятно познакомиться!\n\nА теперь введи текст')
    await MessageInfo.fill_message.set()

@dp.message_handler(state = MessageInfo.fill_message) #получение и обработка текста
async def get_user_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text
    keyboard_back: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_back: InlineKeyboardButton = InlineKeyboardButton(text="<<", callback_data = 'go_back_to_text')
    keyboard_back.add(button_back)
    await message.answer(text='Супер!\n\nОтправляй почту',reply_markup = keyboard_back)
    await MessageInfo.fill_mail.set()

@dp.message_handler(lambda message: isValid(message.text), state = MessageInfo.fill_mail) #получение и обработка почты
async def get_user_mail(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['mail'] = message.text
    await state.finish()
    skeyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    sbutton_1: InlineKeyboardButton = InlineKeyboardButton(text="Да", callback_data = 'photo_yes')
    sbutton_2: InlineKeyboardButton = InlineKeyboardButton(text="Нет", callback_data = 'photo_no')
    skeyboard.add(sbutton_1, sbutton_2)
    await message.answer(text='Сделано!\n\nНужно ли отправить фотографию?', reply_markup=skeyboard)

@dp.message_handler(commands = ['help']) #функция для хелпа (пока хз зачем)
async def send_help_message(message: types.Message):
    print(message)
    name = message.from_user.first_name
    user_id = message.from_user.id
    await bot.send_message(user_id, 'пока ничем помочь не могу')

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
        await bot.send_message(user_id, 'Чтобы вернуться в начало, введи /send')
        await state.finish()
    except Exception as error:
        print(str(error))

@dp.message_handler(lambda message: not message.photo, state = MessageInfo.fill_photo) #проверка фотографии
async def check_photo(message: types.Message):
    await message.reply(text = 'Это не фотография, пришли фотографию')

@dp.message_handler(content_types='any', state = MessageInfo.fill_name) #проверка имени
async def check_name(message: types.Message):
    await message.reply(text = 'Что-то не похоже на имя')

@dp.message_handler(state = MessageInfo.fill_mail) #проверка почты
async def check_mail(message: types.Message):
    await message.reply(text = 'Почта введена некорректно')

@dp.message_handler(content_types = ['any'])
async def get_text(message: types.Message):
    text = message.text
    await bot.send_message(message.from_user.id, 'Выбери команду, которая тебе нужна')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=set_main_menu)