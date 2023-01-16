from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from environs import Env
from email.mime.text import MIMEText
from email.header import Header
import psycopg2
import smtplib

import validation
import config

env = Env()
env.read_env()
TOKEN = env('TOKEN')
mail_login = env('login')
mail_password = env('password')

storage: MemoryStorage = MemoryStorage()

bot = Bot(token = TOKEN)
dp = Dispatcher(bot = bot, storage = storage)

test_dict: dict[str,str] = {} #словарь с данными

class MessageInfo(StatesGroup): #состояние данных пользователя
    null_state = State()
    fill_name = State()
    fill_message = State()
    fill_photo = State()
    fill_mail = State()

async def set_main_menu(dp: Dispatcher):
    main_menu_commands = [
        types.BotCommand(command = '/send', description = 'Вернуться в начало'),
        types.BotCommand(command = '/help', description = 'Помощь'),
        types.BotCommand(command = '/cancel', description = 'Завершить заполнение' )
    ]
    await dp.bot.set_my_commands(main_menu_commands)

@dp.message_handler(commands = ['start']) #приветствие пользователя
async def send_start_message(message: types.Message):
    name = message.from_user.first_name
    await message.answer(text = f'Привет, {name}\n\nЧтобы начать работу, введи /send')

@dp.message_handler(commands = ['help'], state = '*') #функция для хелпа (пока хз зачем)
async def send_help_message(message: types.Message, state: FSMContext):
    await message.answer(text = 'Пока ничем помочь не могу')

@dp.message_handler(commands = ['cancel'], state = '*')
async def cancel_command(message: types.Message, state: FSMContext):
    if await state.get_state() == None:
        await message.answer(text = 'Ты не начал заполнение формы\n\nЧтобы заполнить форму, введи /send')
    else:
        await message.answer(text = 'Ты вышел из отправки сообщений\n\nЧтобы заново заполнить форму, введи\n/send')
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
            await callback.message.edit_text(text = 'Напиши имя отправителя\n\nЧтобы отменить заполнение, введи\n/cancel')
            await MessageInfo.fill_name.set()
        case 'photo_no':  #добавить config с строками
            await callback.message.edit_text(text = 'Сообщение отправлено, чтобы вернуться в начало, введи /send')
        case 'photo_yes':
            await callback.message.edit_text(text = 'Отправь мне фотографию\n\nЧтобы отменить заполнение, введи\n/cancel')
            await MessageInfo.fill_photo.set()
        case 'go_back_to_name':
            await MessageInfo.fill_name.set()
            await callback.message.answer(text = 'Введи имя отправителя\n\nЧтобы отменить заполнение, введи\n/cancel')
        case 'go_back_to_text':
            await MessageInfo.fill_message.set()
            await callback.message.answer(text = 'Введи текст сообщения\n\nЧтобы отменить заполнение, введи\n/cancel')
        case 'go_back_to_mail':
            await MessageInfo.fill_mail.set()
            await callback.message.answer(text = 'Введи почту\n\nЧтобы отменить заполнение, введи\n/cancel')

@dp.message_handler(lambda message: message.text.isalpha() and len(message.text)>1, state = MessageInfo.fill_name) #получение и обработка имени
async def get_user_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id'] = message.from_user.id
        data['name'] = message.text
    keyboard_back: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_back: InlineKeyboardButton = InlineKeyboardButton(text="<<", callback_data = 'go_back_to_name')
    keyboard_back.add(button_back)
    await message.answer(text='Приятно познакомиться!\n\nА теперь введи текст\n\nЧтобы отменить заполнение, введи\n/cancel', reply_markup = keyboard_back)
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

@dp.message_handler(lambda message: validation.isValid(message.text), state = MessageInfo.fill_mail) #получение и обработка почты
async def get_user_mail(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['mail'] = message.text
    test_dict = await state.get_data()
    await state.finish()
    skeyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    sbutton_1: InlineKeyboardButton = InlineKeyboardButton(text="Да", callback_data = 'photo_yes')
    sbutton_2: InlineKeyboardButton = InlineKeyboardButton(text="Нет", callback_data = 'photo_no')
    sbutton_3: InlineKeyboardButton = InlineKeyboardButton(text="<<", callback_data = 'go_back_to_mail')
    skeyboard.add(sbutton_1, sbutton_2).add(sbutton_3)
    await gmail_send(test_dict)
    await message.answer(text='Сделано!\n\nНужно ли отправить фотографию?\n\nЧтобы отменить заполнение, введи\n/cancel', reply_markup=skeyboard)


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
        await bot.send_message(user_id, 'Сообщение отправлено, чтобы вернуться в начало, введи /send')
        await state.finish()
    except Exception as error:
        print(str(error))

@dp.message_handler(content_types = 'any', state = MessageInfo.fill_photo) #проверка фотографии
async def check_photo(message: types.Message):
    await message.reply(text = 'Это не фотография, пришли фотографию\n\nЧтобы отменить заполнение, введи\n/cancel')

@dp.message_handler(content_types='any', state = MessageInfo.fill_name) #проверка имени
async def check_name(message: types.Message):
    await message.reply(text = 'Что-то не похоже на имя\n\nЧтобы отменить заполнение, введи\n/cancel')

@dp.message_handler(state = MessageInfo.fill_mail) #проверка почты
async def check_mail(message: types.Message):
    await message.reply(text = 'Почта введена некорректно\n\nЧтобы отменить заполнение, введи\n/cancel')

@dp.message_handler(content_types = ['any'])
async def get_text(message: types.Message):
    text = message.text
    await message.answer(text = 'Выбери команду, которая тебе нужна')

async def gmail_send(test_dict):
    try:
        new_text = f'От: {test_dict["name"]}\n\n{test_dict["message"]}\n\nСообщение отправлено с помощью телеграм бота t.me/samiy_tupoi_bot'
        new_text = MIMEText(new_text, 'plain', 'utf-8')
        new_text['Subject'] = Header('Message from Telegram bot','utf-8')
        server = smtplib.SMTP('smtp.gmail.com', 587) #подключение к почте
        server.starttls()
        server.login(mail_login ,mail_password)
        server.sendmail(mail_login,test_dict['mail'],new_text.as_string())
        server.quit()
        print('[INFO] Message was sended')
        await database(test_dict)
    except Exception as er:
        print('[INFO] Error while sending message', er)

async def database(test_dict):
    try:
        connection = psycopg2.connect( #подключение к БД
        host = config.host,
        user = config.user,
        password = config.password,
        database = config.db_name
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute('SELECT VERSION()')
            print(cursor.fetchone())
        with connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO users (user_id, user_name, user_text, user_mail) VALUES ({test_dict['user_id']},'{test_dict['name']}','{test_dict['message']}', '{test_dict['mail']}');")
            print('[INFO] Data was added')
    except Exception as er:
        print('[INFO] Error while working with PostgreSQL', er)
    finally:
        if connection:
            connection.close()
            print('[INFO] PostgreSQL connection closed')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=set_main_menu)