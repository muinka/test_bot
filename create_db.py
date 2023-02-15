from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from environs import Env

import logging

logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="a", format="%(asctime)s %(levelname)s %(message)s")

meta = MetaData()

en = Env()
en.read_env()
db_url = en('db_url')
users = Table('users', meta, Column('user_id', Integer),
Column('user_name', String), Column('user_text', String), Column('user_mail', String))

try:
    engine = create_engine(db_url)
    meta.create_all(engine)
    connection = engine.connect()
    logging.info('Connection with PostgreSQL done')
except Exception as error:
    logging.error('Error while connecting to PostgreSQL', error)

def insert(user_dict):
    product_query = users.insert().values(user_id = user_dict['user_id'],
    user_name = user_dict['name'],
    user_text = user_dict['message'],
    user_mail = user_dict['mail'])
    logging.info('Insert to PostgreSQL done')
    try:
        connection.execute(product_query)
        connection.commit()
    except Exception as error:
        logging.error('Error while inserting in PostgreSQL', error)