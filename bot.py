from config import *
import validation
import create_db
import send_mail

env = Env()
env.read_env()
TOKEN = env('TOKEN')
mail_login = env('login')
mail_password = env('mail_key')
host = env('host')
user = env('user')
db_pass = env('password')
db_name = env('db_name')

storage: MemoryStorage = MemoryStorage()

bot = Bot(token = TOKEN)
dp = Dispatcher(bot = bot, storage = storage)

logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="a", format="%(asctime)s %(levelname)s %(message)s")

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

#приветствие пользователя
async def send_start_message(message: types.Message):
    name = message.from_user.first_name
    await message.answer(text = f'Привет, {name}\n\nЧтобы начать работу, введи /send')

#функция для хелпа (пока хз зачем)
async def send_help_message(message: types.Message, state: FSMContext):
    await message.answer(text = 'Пока ничем помочь не могу')

#функция отмены отправки сообщения
async def cancel_command(message: types.Message, state: FSMContext):
    if await state.get_state() == None:
        await message.answer(text = 'Ты не начал заполнение формы\n\nЧтобы заполнить форму, введи /send')
    else:
        await message.answer(text = 'Ты вышел из отправки сообщений\n\nЧтобы заново заполнить форму, введи\n/send')
        await state.reset_state()

#начало заполнения анкеты
async def form_start(message: types.Message):
    keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_1: InlineKeyboardButton = InlineKeyboardButton(text="Поехали", callback_data = 'first_step')
    keyboard.add(button_1)
    await message.answer(text = 'Я умею отправлять сообщения на почту, начнем?', reply_markup=keyboard)

#Обработка коллбеков
async def get_callback(callback: types.CallbackQuery, state: FSMContext):
    user_dict = await state.get_data()
    match callback.data:
        case 'first_step':
            await callback.message.edit_text(text = 'Напиши имя отправителя\n\nЧтобы отменить заполнение, введи\n/cancel')
            await MessageInfo.fill_name.set()
        case 'photo_no':  #добавить config с строками
            flag = True
            send_mail.no_photo(user_dict,flag)
            await callback.message.edit_text(text = 'Сообщение отправлено, чтобы вернуться в начало, введи /send')
            await state.finish()
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

#получение и обработка имени
async def get_user_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id'] = message.from_user.id
        data['name'] = message.text
    keyboard_back: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_back: InlineKeyboardButton = InlineKeyboardButton(text="<<", callback_data = 'go_back_to_name')
    keyboard_back.add(button_back)
    await message.answer(text='Приятно познакомиться!\n\nА теперь введи текст\n\nЧтобы отменить заполнение, введи\n/cancel', reply_markup = keyboard_back)
    await MessageInfo.fill_message.set()

#получение и обработка текста
async def get_user_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message'] = message.text
    keyboard_back: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_back: InlineKeyboardButton = InlineKeyboardButton(text="<<", callback_data = 'go_back_to_text')
    keyboard_back.add(button_back)
    await message.answer(text='Супер!\n\nОтправляй почту',reply_markup = keyboard_back)
    await MessageInfo.fill_mail.set()

#получение и обработка почты
async def get_user_mail(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['mail'] = message.text
    skeyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    sbutton_1: InlineKeyboardButton = InlineKeyboardButton(text="Да", callback_data = 'photo_yes')
    sbutton_2: InlineKeyboardButton = InlineKeyboardButton(text="Нет", callback_data = 'photo_no')
    sbutton_3: InlineKeyboardButton = InlineKeyboardButton(text="<<", callback_data = 'go_back_to_mail')
    skeyboard.add(sbutton_1, sbutton_2).add(sbutton_3)
    await message.answer(text='Сделано!\n\nНужно ли отправить фотографию?\n\nЧтобы отменить заполнение, введи\n/cancel', reply_markup=skeyboard)

#функция дли обработки фоток
async def get_user_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_dict = await state.get_data()
    await message.photo[-1].download(destination_file=f'photos/{user_id}/photo.jpg')
    flag = True
    logging.info('Data saved')
    send_mail.with_photo(user_dict, flag)
    #await bot.send_photo(user_id, photo) для теста, получается ли фотка нормально
    await bot.send_message(user_id, 'Сообщение отправлено, чтобы вернуться в начало, введи /send')
    await state.finish()

#проверка фотографии
async def check_photo(message: types.Message):
    await message.reply(text = 'Это не фотография, пришли фотографию\n\nЧтобы отменить заполнение, введи\n/cancel')

#проверка имени
async def check_name(message: types.Message):
    await message.reply(text = 'Что-то не похоже на имя\n\nЧтобы отменить заполнение, введи\n/cancel')

#проверка почты
async def check_mail(message: types.Message):
    await message.reply(text = 'Почта введена некорректно\n\nЧтобы отменить заполнение, введи\n/cancel')

#остальные запросы
async def get_text(message: types.Message):
    await message.answer(text = 'Выбери команду, которая тебе нужна')

#регистрируем хэндлеры
dp.register_message_handler(send_start_message, commands='start')

dp.register_message_handler(send_help_message, commands='help', state='*')

dp.register_message_handler(cancel_command,commands='cancel',state='*')

dp.register_message_handler(form_start,commands='send')

dp.register_callback_query_handler(get_callback, state='*')

dp.register_message_handler(get_user_name,lambda message: message.text.replace(" ","").isalpha() and len(message.text)>1, state = MessageInfo.fill_name )

dp.register_message_handler(get_user_message, state = MessageInfo.fill_message)

dp.register_message_handler(get_user_mail, lambda message: validation.isvalid(message.text), state = MessageInfo.fill_mail)

dp.register_message_handler(get_user_photo,content_types = 'photo', state = MessageInfo.fill_photo)

dp.register_message_handler(check_photo, content_types = 'any', state = MessageInfo.fill_photo)

dp.register_message_handler(check_name, content_types='any', state = MessageInfo.fill_name)

dp.register_message_handler(check_mail,state = MessageInfo.fill_mail)

dp.register_message_handler(get_text,content_types = 'any')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=set_main_menu)