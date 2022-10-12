from telethon.tl.types import MessageEntityTextUrl
from glob import glob
from dateutil.relativedelta import relativedelta  # pip3 install python-dateutil

import datetime
import os


def get_channel_id(client, link):  # получение ID канала
    m = client.get_messages(link, limit=1)
    channel_id = m[0].peer_id.channel_id
    return str(channel_id)


def clearify_text(msg):  # очищение текста от символов гиперссылки
    text = msg.message
    text_splitted = text.split()
    text_listed = [word for word in text_splitted if word != ' ']
    return " ".join(text_listed)


def get_message_content(client, msg, url, channel_name, directory_name):  # получение содержимого сообщения
    msg_date = str(msg.date)  # дата отправки сообщения
    msg_url = url + '/' + str(msg.id)  # каст ссылки на сообщение
    file = open(f"{channel_name}/{directory_name}/{directory_name}_meta.txt", 'a+')  # запись метаданных сообщения
    file.write(msg_url)
    file.write('\n' + msg_date)
    file.close()
    if msg.message:  # если сообщение содержит текст, запись этого текста в текстовый файл в папке сообщения
        text = clearify_text(msg=msg)
        file = open(f"{channel_name}/{directory_name}/{directory_name}.txt", "w")
        file.write(text)
        file.close()
    if msg.media:  # если сообщение содержит медиа (фото, видео, документы, файлы), загрузка медиа в папку сообщения
        client.download_media(message=msg, file=f"{channel_name}/{directory_name}")
    if msg.entities:  # запись гиперссылок из текста сообщения в файл сообщения
        urls = [ent.url for ent in msg.entities if isinstance(ent, MessageEntityTextUrl)]
        file = open(f"{channel_name}/{directory_name}/{directory_name}.txt", mode='a+')
        for u in urls:
            file.write('\n' + u)
        file.close()


def find_last_parsed_date(path):  # определение даты, с которой начинать парсинг
    paths = glob(f"{path}/*/*meta.txt", recursive=True)  # поиск существующих метаданных по уже собранным сообщениям
    oldest = datetime.datetime.strptime("1970-01-01 00:00:00+00:00", "%Y-%m-%d %H:%M:%S%z")
    temp = oldest
    for p in paths:  # поиск даты отправки последнего сообщения
        with open(p, 'r') as file:
            date = datetime.datetime.strptime(file.readlines()[-1], "%Y-%m-%d %H:%M:%S%z")
            if date > oldest:
                oldest = date
    if temp == oldest:
        oldest = datetime.datetime.now() - relativedelta(months=3)  # если сообщений нет, офсет устанавливается на
                                                                    # три месяца от текущей даты
    return oldest


def parse(client, url):  # сбор сообщений из канала
    err = []  # переменная возможной ошибки
    channel_id = get_channel_id(client, url)  # получение ID канала
    os.makedirs(channel_id, exist_ok=True)  # создание папки канала в текущей директории
    oldest = find_last_parsed_date(channel_id)  # получение даты, с которой начинать парсинг
    for message in client.iter_messages(url, reverse=True, offset_date=oldest):  # итератор по сообщениям (урл - ссылка
                                                                                 # на канал, реверс - итерация от старых
                                                                                 # к новым, офсет - дата с которой
                                                                                 # начинать парсинг
        try:
            directory_name = str(message.id)  # получение ID сообщения
            os.makedirs(f"{channel_id}/{directory_name}", exist_ok=True)  # создание папки сообщения
            get_message_content(client, message, url, channel_id, directory_name)  # обработка сообщения

        except Exception as passing:  # обработка ошибок
            err.append(passing)
            continue
    return err  # возврат возможных ошибок
