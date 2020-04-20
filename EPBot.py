from typing import Dict

import telebot
import apiai, json
import EPStatistics as es
import random
import time
import datetime
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload,MediaFileUpload
from googleapiclient.discovery import build
import pprint
import io


cpublic_messages_to_answer = 9
cbot_name = '@EPUUBot'
c_id_data_json = '1DJ3-_pZBpagkBUmwkXvmRQdudeLoCN13'
bot = telebot.TeleBot('1010057424:AAF23brU8OJcRUkOnMKoLgwDmb-3aj21UPw')

def get_random_message(aconfig, section_name):
    random.seed()
    return aconfig[section_name][str(random.randint(1,len(aconfig[section_name])))]

@bot.message_handler(commands=['start'])
def start_message(message):
    # загружаем данные о титанах и войнах
    global data
    with open('data.json', "r", encoding='utf-8') as read_file:
        data = json.load(read_file)

    bot.send_message(message.chat.id, 'Данные перезагружены, можно запрашивать статистику командами\n'
                                      '/titantotal <маска даты [YYYY-MM-DD]> - урон по титану (сортировка по суммарному урону)\n'
                                      '/titanavg <маска даты [YYYY-MM-DD]> - урон по титану (сортировка по среднему урону)\n'
                                      '/wartotal <маска даты [YYYY-MM-DD>] - очков в войнах (сортировка по сумме очков)\n'
                                      '/waravg <маска даты [YYYY-MM-DD>] - очков в войнах (сортировка по среднему)\n'
                                      'P.S. Для продвинутых: в масках поддерживаются регулярные выражения')

@bot.message_handler(regexp=r'(titan|war)(total|avg)')
def start_message(message):
    print(message.text)
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
    #определяем персональное ли это сообщение для бота (в тексте встречается имя бота; ответ на сообщение бота; приватный чат с ботом)
    to_bot = False
    if message.reply_to_message is not None:
        if message.reply_to_message.from_user.username is not None:
            to_bot = '@'+message.reply_to_message.from_user.username == cbot_name
    to_bot = (message.text.find(cbot_name) >= 0) | (message.chat.type == 'private') | to_bot

    if not to_bot:
        msg_count += 1
    if (msg_count >= cpublic_messages_to_answer) | to_bot:
        request = apiai.ApiAI('1768a604bffd462292b221630bd7d66b').text_request()
        request.lang = 'ru'
        request.session_id = 'EPUUBot'
        request.query = message.text.replace(cbot_name,'')
        responseJson = json.loads(request.getresponse().read().decode('utf-8'))
        response = responseJson['result']['fulfillment']['speech']

        reply_to_message_id = None #по умолчанию не отвечаем на сообщение
        if message.chat.type != 'private':
            reply_to_message_id = message.message_id  #отвечаем на сообщение если чат не приватный

        if response:
            bot.send_message(message.chat.id, text=response, reply_to_message_id=reply_to_message_id)
            if not to_bot:
                msg_count = 0
        elif to_bot:
            bot.send_message(message.chat.id, text=get_random_message(dconfig, 'nothing_to_say'), reply_to_message_id=reply_to_message_id)
    print(msg_count)

# # загружаем данные о титанах и войнах
# with open('data.json', "r", encoding='utf-8') as read_file:
#     data = json.load(read_file)

#загружаем config
with open('config.json', 'r', encoding='utf-8') as fconfig:  # открываем файл на чтение
    dconfig = json.load(fconfig)

pp = pprint.PrettyPrinter(indent=4)
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'epbot-274622-530f5ad65b26.json'
credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)
results = service.files().list(
    pageSize=1000,
    fields="nextPageToken, files(id, name, mimeType, parents, createdTime)",
    q="name contains 'data.json'").execute()

if len(results.get('files')) == 0:
    print('Not found data.json. Bot stopped')
    raise SystemExit(1)

file_id = '1DJ3-_pZBpagkBUmwkXvmRQdudeLoCN13'
request = service.files().get_media(fileId=file_id)
filename = 'data.txt'
fh = io.FileIO(filename, 'w')
print('Loading data.json...')
downloader = MediaIoBaseDownload(fh, request)
done = False
while done is False:
    status, done = downloader.next_chunk()
    print ("Download %d%%." % int(status.progress() * 100))

# загружаем данные о титанах и войнах
with open('data.txt', "r", encoding='utf-8') as read_file:
    data = json.load(read_file)

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
