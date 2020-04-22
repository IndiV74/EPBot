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
import io
import os
from boto.s3.connection import S3Connection
#import pprint

cpublic_messages_to_answer = 9
cbot_name = '@EPUUBot'
c_id_data_json = '1DJ3-_pZBpagkBUmwkXvmRQdudeLoCN13'
c_id_config_json = '1SW0R1o8uNX9FmtL6aMLgvB9TqTP--ygw'
bot = telebot.TeleBot('1010057424:AAF23brU8OJcRUkOnMKoLgwDmb-3aj21UPw')

def get_random_message(aconfig, section_name):
    random.seed()
    return aconfig[section_name][str(random.randint(1,len(aconfig[section_name])))]

def load_dictonary_from_GoogleDrive(file_id, fileName):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_INFO = dict()
    try:
        #пытаемся загрузить файл учетных данных Google Drive (для локального запуска)
        with open('epbot-274622-530f5ad65b26.json', 'r', encoding='utf-8') as fSERVICE_ACCOUNT_INFO:
            SERVICE_ACCOUNT_INFO = json.load(fSERVICE_ACCOUNT_INFO)
            print(SERVICE_ACCOUNT_INFO)
    except FileNotFoundError:
        pass
        # загружаем учетные данные Google Drive из heroku Config Vars
        GC = os.getenv('GOOGLE_CREDENTIALS')
        SERVICE_ACCOUNT_INFO= json.loads(GC)
        # SERVICE_ACCOUNT_INFO['type'] = os.environ['type']
        # SERVICE_ACCOUNT_INFO['project_id'] = os.environ['project_id']
        # SERVICE_ACCOUNT_INFO['private_key_id'] = os.environ['private_key_id']
        # SERVICE_ACCOUNT_INFO['private_key'] = r'-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDGgQr+sKPPVcPf\n7lKjBPzaHCT+BxT3Uk9LGltbgowhq6a0xRukZ5m1exfsiVMwcD8tTfxKlrE9hhet\niWSaecFOy003Gl8XWaGvERs1NB62G1glfQgxsAaO7UL0BOOPExbK+R5ZAHrGvp26\ngQaZ5td3J7QZAH+uAjZr+tVoj9hYdwrX23oXIY/zry/WFCU7NhQDwYqwvovuZzsu\nPJRPV6I+9qUeIs46NhJCa0j8GrbXZIYIM+JPOX4pXcf27nzT0NYns6zm3krVGRM4\nvmfWVQKkbKb8ofbbqmrJp49U1KOmU7iwHq9qyt6A0G4SNA4+6dDJb7+bdHrUDOLU\ngC6qNMHpAgMBAAECggEAAM94kFD0FBOxocg2pqhTcSJAU/VFCOTTkS+5nIiOb5bY\n116Y6wtBsUjUfCb9eBJohRP9uhZSu5uvSzMP4Rw2jk6jxa2paFE/bsPXLrXbbIPG\nkLHj0/hJZXogGMj+mPAxQ20EoblBb8vJ7wWQ+ImofDnCP9Fti0tOEFlLnXA9c8Sj\ntqHyLXlWCQZ4Llfi4X2QsfFA1ERrE2UlhiAXRcDgiE262zD5tzZu1bpRTPZeTKX4\nD8AsyebGr0MUkjjS7NBSRNgm+9fmcYxqQfVEPNfz57J8bzfTqKTYOKN6FbxDzoy/\nL2s5+8213bu1HdyRNczeeRsRqszohzdbpocT7TF6vQKBgQD4KAOHFS1O81gycH3/\nCvaA4FkZg8L7DKXa4Lbf9OiN9IZLkX57o0FB/pwJKpeCFScQIjNJB9/f6PFxlDjf\ncIGP7TwX95SlR1UNEAMRk68tnwnFmLgLaM7scr9xnMvCGm2tU2nhFjqVK+DKuq3V\nwjFAVEHnFOCuCiP+Z/IFECNJXQKBgQDMx0Mi5pYRpMS7xs7MC1WC8/eRDjdnvtwi\nZYFo6u+1ShRCqZI2GSFB91cEffXEeZ31VFkEthPB1Tq5NWKa7fUFI+gDk2Wj6CQw\nxQJinVu6QxfShG7an+Mq/Iq/g3gmzn6kHLWNOEMavk44AmRWy6pSKWFhZyCm5if+\nCjmTemk1/QKBgB64TV9+lqJMa6Gq3V4iTEu9+im3bv7HHQ0QfnMRDWztVWardz31\nAtIZo9VaqXDYD4LmyPSEfglo++K0l6nJcrCPjL3mz0b6oqPAVLDrWGdMZdhJRJdc\n/Si2N87nuy2nOeaYCeZsawomaWiPXY+1v4UYKSRjKEFDThtjYMmRqtydAoGABlVn\nay3smFEbUJ9+h+sV0v4OuyrQZeIOVvYCwab6kQXgiItMHWY7lBm9VEM9Fb2ZOBxK\nwI2NIOKidVYEXbxcZrNMmse1ThOBAw0k3L33N1SZ6QX1k8d8NDkpZXEAh1q9qf/F\nUb/au3oFW1AfoFueQfpLq8KPzPmzZPUWAMy5clUCgYA+8AP8ALyKIqAZmdI2+jH1\nkjBx6IEkhHy6dyd7WQLBnRypbnBvgooZ9a46ivwxfb580LVK3suWPHuNIIqZzS97\nYPoPTrdlwlQ+GYGPIEMI/uJGkhwBKuZ+pLEFz4F++s0UKcdVRgdZac6v+GztJ/aP\nxI8K0mdk9s7jE3QpYxYLzw==\n-----END PRIVATE KEY-----\n'
        # # SERVICE_ACCOUNT_INFO['private_key'] = os.environ['private_key']
        # SERVICE_ACCOUNT_INFO['client_email'] = os.environ['client_email']
        # SERVICE_ACCOUNT_INFO['client_id'] = os.environ['client_id']
        # SERVICE_ACCOUNT_INFO['auth_uri'] = os.environ['auth_uri']
        # SERVICE_ACCOUNT_INFO['token_uri'] = os.environ['token_uri']
        # SERVICE_ACCOUNT_INFO['auth_provider_x509_cert_url'] = os.environ['auth_provider_x509_cert_url']
        # SERVICE_ACCOUNT_INFO['client_x509_cert_url'] = os.environ['client_x509_cert_url']

    print(SERVICE_ACCOUNT_INFO)
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


# pp = pprint.PrettyPrinter(indent=4)

# d = {
#     'private_key_id': '530f5ad65b2622cb11904ab12b0a2c618bcaacad',
#     'private_key': '-----BEGIN PRIVATE KEY-----\\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDGgQr+sKPPVcPf\\n',
#     }
#
# private_key = d['private_key']
# print(private_key)
# private_key = "\n".join(filter(bool, private_key.splitlines()))
# print(private_key)
# print(private_key[1])
# private_key = private_key.replace('\\\\',"\\")
# print(f'd={d}')
# print(f"d[private_key]={d['private_key']}")
# print(f"private_key={private_key}")
# d['private_key']=private_key
# print(f'd={d}')

data = load_dictonary_from_GoogleDrive(c_id_data_json, 'data.json')
dconfig = load_dictonary_from_GoogleDrive(c_id_config_json, 'config.json')

#pp.pprint(dconfig)

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
