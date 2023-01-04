import time
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

TOKEN = '5630269099:AAGYTYb8FCm_7e1nGGG6_v83FHlrUug87yU'

bot = Bot(token = TOKEN)
dp = Dispatcher(bot = bot)

@dp.message_handler(commands = ['start']) #функция старта
async def send_start_message(message: types.Message):
    print(message)
    name = message.from_user.first_name
    user_id = message.from_user.id
    await bot.send_message(user_id, f'Привет, <u>{name}</u>',parse_mode='html')
    await bot.send_message(user_id, 'Я могу отправить сообщение с фотографией или просто текст')
    keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
    button_1: InlineKeyboardButton = InlineKeyboardButton(text="Текст с фото", callback_data = 'with_photo')
    button_2: InlineKeyboardButton = InlineKeyboardButton(text="Текст без фото", callback_data = 'without_photo')
    keyboard.add(button_1,button_2)
    await bot.send_message(user_id, 'Выбери, что тебе нужно', reply_markup=keyboard)

@dp.callback_query_handler() #узнать, есть ли фото в сообщении
async def with_photo_callback(callback: types.CallbackQuery):
    if callback.data == 'with_photo':
        await bot.send_message(callback.from_user.id, 'Ты выбрал сообщение с фото')
        await bot.send_message(callback.from_user.id, 'Пришли текст своего сообщения')

    else:
        await bot.send_message(callback.from_user.id, 'Ты выбрал только текст')
        await bot.send_message(callback.from_user.id, 'Пришли текст своего сообщения')
        

@dp.message_handler(commands = ['help']) #функция для хелпа (пока хз зачем)
async def send_help_message(message: types.Message):
    print(message)   
    name = message.from_user.first_name
    user_id = message.from_user.id
    await bot.send_message(user_id, message)

@dp.message_handler(content_types = ['photo']) #функция дли сохранения фотки (сделаю потом)
async def get_user_photo(message: types.Message):
    user_id = message.from_user.id
    photo_id = message.photo[2].file_id
    try:
        file = await bot.get_file(photo_id)
        file_path = file.file_path
        await bot.download_file(file_path, 'photo.jpg')
        photo = open('photo.jpg', 'rb')
        await bot.send_photo(user_id, photo)
    except Exception as error:
        print(str(error))

@dp.message_handler(content_types = ['text'])
async def get_text(message: types.Message):
    text = message.text
    print(text)
    await bot.send_message(message.from_user.id, 'Введите почтовый адрес получателя')

if __name__ == '__main__':
    executor.start_polling(dp)