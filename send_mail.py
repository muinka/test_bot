import yagmail
import logging
import time
from environs import Env

import create_db

logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="a", format="%(asctime)s %(levelname)s %(message)s")

env = Env()
env.read_env()
mail_login = env('login')
mail_password = env('mail_key')
try:
    yag = yagmail.SMTP(mail_login,mail_password)
    logging.info('Connection with GMail done')
except Exception as er:
    logging.error('Error while connecting to GMail', er)

def no_photo(user_dict,flag):
    if flag:
        try:
            yag.send(user_dict['mail'],'Telegram Bot',f'{user_dict["message"]}\n\nОтправлено с помощью Бота Телеграм', headers={'From': f'Telegram Bot <{mail_login}>'})
            logging.info('Mail sended after first try')
            create_db.insert(user_dict)
        except Exception as error:
            logging.error('Error with Mail sending after first try', error)
            time.sleep(2)
            try:
                yag.send(user_dict['mail'],'Telegram Bot',f'{user_dict["message"]}\n\nОтправлено с помощью Бота Телеграм', headers={'From': f'Telegram Bot <{mail_login}>'})
                logging.info('Mail sended')
                create_db.insert(user_dict)
            except Exception as error:
                logging.error('Error with Mail sending after second try', error)
    else:
        logging.error('No data to send')

def with_photo(user_dict,flag):
    photo_path = f'photos/{user_dict["user_id"]}/photo.jpg'
    if flag:
        try:
            yag.send(user_dict['mail'],'Telegram Bot',f'{user_dict["message"]}\n\nОтправлено с помощью Бота Телеграм', headers={'From': f'Telegram Bot <{mail_login}>'}, attachments=photo_path)
            logging.info('Mail sended after first try')
            create_db.insert(user_dict)
        except Exception as error:
            logging.error('Error with Mail sending after first try', error)
            time.sleep(2)
            try:
                yag.send(user_dict['mail'],'Telegram Bot',f'{user_dict["message"]}\n\nОтправлено с помощью Бота Телеграм', headers={'From': f'Telegram Bot <{mail_login}>'}, attachments=photo_path)
                logging.info('Mail sended')
                create_db.insert(user_dict)
            except Exception as error:
                logging.error('Error with Mail sending after second try', error)
    else:
        logging.error('No data to send')
