import telebot
import apiai, json
import EPStatistics as es
import random
import time
import datetime
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
from googleapiclient.discovery import build
import io
import os
import re
#from langdetect import detect
#import pprint

cpublic_messages_to_response = 9
cbot_name = '@EPUUBot'
c_id_data_json = '1DJ3-_pZBpagkBUmwkXvmRQdudeLoCN13'
c_id_config_json = '1SW0R1o8uNX9FmtL6aMLgvB9TqTP--ygw'
bot = telebot.TeleBot('1010057424:AAF23brU8OJcRUkOnMKoLgwDmb-3aj21UPw')

def get_random_message(section_name):
    global dconfig
    random.seed()
    return dconfig[section_name][str(random.randint(1,len(dconfig[section_name])))]

def load_dictonary_from_GoogleDrive(file_id, fileName):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    try:
        #пытаемся загрузить файл учетных данных Google Drive (для локального запуска)
        with open('epbot-274622-530f5ad65b26.json', 'r', encoding='utf-8') as fSERVICE_ACCOUNT_INFO:
            SERVICE_ACCOUNT_INFO = json.load(fSERVICE_ACCOUNT_INFO)
    except FileNotFoundError:
        # загружаем учетные данные Google Drive из heroku Config Vars
        SERVICE_ACCOUNT_INFO = json.loads(os.getenv('GOOGLE_CREDENTIALS'))

    credentials = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)

    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(fileName, 'w')
    print(f'Loading {fileName}...')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print ("Download %d%%." % int(status.progress() * 100))

    # загружаем данные о титанах и войнах
    with open(fileName, "r", encoding='utf-8') as read_file:
        a_dict = json.load(read_file)
    return a_dict

def get_bot_response(message):
    request = apiai.ApiAI('1768a604bffd462292b221630bd7d66b').text_request()
    # try:
    #     request.lang = 'uk' if detect(message.text) == 'uk' else 'ru'
    # except:
    #     request.lang = 'ru'
    request.lang = 'ru'
    request.session_id = 'EPUUBot'
    request.query = message.text.replace(cbot_name, '')[0:255]
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    # если успешно
    if responseJson['status']['code'] == 200:
        response = responseJson['result']['fulfillment']['speech']
    else:
        print(responseJson['status'])
        response = None
    # признак того, что бот не нашел ответа (нужен для счетчика обработанных сообщений)
    null_response = False if response else True
    return (response if response else get_random_message('nothing_to_say')), null_response


@bot.message_handler(commands=['start'])
def start_message(message):
    # загружаем данные о титанах и войнах
    global data, dconfig
    data = load_dictonary_from_GoogleDrive(c_id_data_json, 'data.json')
    dconfig = load_dictonary_from_GoogleDrive(c_id_config_json, 'config.json')

    bot.send_message(message.chat.id, 'Данные перезагружены, можно запрашивать статистику командами\n'
                                      '/titantotal <маска даты [YYYY-MM-DD]> - урон по титану (сортировка по суммарному урону)\n'
                                      '/titanavg <маска даты [YYYY-MM-DD]> - урон по титану (сортировка по среднему урону)\n'
                                      '/wartotal <маска даты [YYYY-MM-DD>] - очков в войнах (сортировка по сумме очков)\n'
                                      '/waravg <маска даты [YYYY-MM-DD>] - очков в войнах (сортировка по среднему)\n'
                                      'P.S. Для продвинутых: в масках поддерживаются регулярные выражения')

@bot.message_handler(regexp=r'(titan|war)(total|avg)')
def start_message(message):
    print(f'{message.from_user.first_name} ({message.from_user.username}): {message.text}')
    cmd = ''
    typeObject = ''
    try:
        cmd = (message.text.split(' ', 1)[0]).split('@', 1)[0]
        cmd = cmd[1:len(cmd)]
        regExpMask = message.text.split(' ', 1)[1]
    except IndexError:
        regExpMask = ''

    if cmd.find('titan') >= 0:
        typeObject = 'titans'
    elif cmd.find('war') >= 0:
        typeObject = 'wars'
    try:
        dSort = {'titantotal': es.cSortTotalPoint,
                 'titanavg': es.cSortAvgPoint,
                 'wartotal': es.cSortTotalPoint,
                 'waravg': es.cSortAvgPoint}

        res = es.statSummary(data, typeObject, regExpMask, dSort[cmd])
    except:
        res = 'Что-то пошло не так... @IndiV! почини меня... пожалуйста 😜'

    bot.send_message(message.chat.id, res)


@bot.message_handler(content_types=['text'])
def start_message(message):
    global msg_count
    # получаем ответ бота в любом случае, даже если не будем отвечать на сообщение (нужно для дальнейшего анализа)
    bot_response, null_response = get_bot_response(message)
    #определяем персональное ли это сообщение для бота (в тексте встречается имя бота; ответ на сообщение бота; приватный чат с ботом)
    to_bot = False
    if message.reply_to_message is not None:
        if message.reply_to_message.from_user.username is not None:
            to_bot = ('@'+message.reply_to_message.from_user.username == cbot_name)
    to_bot = (message.text.find(cbot_name) >= 0) | (message.chat.type == 'private') | to_bot | (re.search('Люс[яеию]', message.text) is not None)

    #если чат не приватный, то запоминаем id сообщения на которое будем отвечать
    reply_to_message_id = None if message.chat.type == 'private' else message.message_id
    if to_bot:
        bot.send_message(message.chat.id, text=bot_response, reply_to_message_id=reply_to_message_id)
    else:
        msg_count += 1
        # отвечаем на сообщение если превышен лимит ожидания и у бота нашелся ответ
        if msg_count >= cpublic_messages_to_response and not null_response:
            bot.send_message(message.chat.id, text=bot_response, reply_to_message_id=reply_to_message_id)
            if not null_response and not to_bot:
                    msg_count = 0

    print(f'{message.from_user.first_name} ({message.from_user.username}): {msg_count}')

data = load_dictonary_from_GoogleDrive(c_id_data_json, 'data.json')
dconfig = load_dictonary_from_GoogleDrive(c_id_config_json, 'config.json')

while True:
    try:
        msg_count = 0
        bot.delete_webhook()
        time.sleep(5)
        print(f'{str(datetime.datetime.now())}: bot.polling...')
        bot.polling(none_stop=True, timeout=5)
    except Exception as e:
        print(f'{str(datetime.datetime.now())}: {e}')
        time.sleep(60)
