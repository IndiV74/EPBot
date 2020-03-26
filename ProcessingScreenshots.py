import datetime as DT
import json
import os
import re
from glob import glob
from os import path
import cv2
import pytesseract

cUnknownObject = 'UnknownObject'
cTitanKilled = 'TitanKilled'
cTitanHid = 'TitanHid'
cTitanUnknown = 'TitanUnknown'
cTitans = 'titans'
cWars = 'wars'


# ищет содержит ли строка NickName один из ников альянса, если да, то возвращает ник (ключ) + оригинальный ник (значение в справочнике), иначе None
def findMembersInAlliance(NickName, AllianceMembers):
    for i, keyMember in enumerate(AllianceMembers.keys()):
        if NickName.find(keyMember) >= 0:
            return (keyMember, AllianceMembers.get(keyMember))
    return (None, None)


""" возвращает дату файла из его названия в формате dateTime. Если дату определить не удалось, возращается 0 и rint с ошибкой """


def extractFileDateTime(fileName):
    # шаблон имени файла 'Screenshot_20200302-224233'
    fileDate = 0
    try:
        sd = re.search('\d{8}-\d{6}', fileName)[0]
        fileDate = DT.datetime.strptime(sd, '%Y%m%d-%H%M%S')
    except (TypeError, ValueError):
        print('Не удалось определить дату файла: ' + fileName)
    return fileDate


# возаращает вид файла (титан или война) и статус титана (повержен, скрылся).
def getActionProperty(text):
    to = re.search(r'^(Титан.+(повержен|скрылся))|(Лучшие.+титанов)|(Лучшие.+войне)', text, flags=re.MULTILINE)
    typeAction = cUnknownObject
    if to:
        if to[0].find('войне') >= 0:
            typeAction = cWars
            titanState = ''
        else:
            typeAction = cTitans
            if to[0].find('повержен') >= 0:
                titanState = cTitanKilled
            elif to[0].find('скрылся') >= 0:
                titanState = cTitanHid
            else:
                titanState = cTitanUnknown
    else:
        typeAction = cUnknownObject
        titanState = None
    # print(to[0], typeAction, titanState)
    return typeAction, titanState


"""распознает заданый файл, парсит и создает список объектов action. Если ошибки в никах - возвращает список нераспознанных ников
   возвращает:
    resText - список урона игроков вида: <ник>: <урон>
    unknownNicks - список нераспознанных ников, если он пустой, значит файл полностью обработан правильно"""


def processingScreenshot(fileName):
    action = dict()
    errorMessage = ''
    global log_text
    print('processing: ' + fileName)
    log_text += f'processing: {fileName} \n'
    if str(extractFileDateTime(path.basename(fileName))) in {**data['titans'], **data['wars']}.keys():
        log_text += 'Файл уже обработан\n'
        print('Файл уже обработан')
        return ('', errorMessage)

    if fileName.find('.jpg') >= 0:
        img = cv2.imread(fileName)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        img = cv2.bitwise_not(img)
        #cv2.imwrite(fileName + 'Final.jpg', img)
        text = pytesseract.image_to_string(img, 'eng+ukr+rus')
    else:  # для исправленных текстовых файлов
        fn = open(fileName, 'r', encoding='utf-8')
        text = fn.read()
        fn.close()

    textSource = text = "\n".join(filter(bool, text.splitlines()))  # Удаляем пустые строки

    # считываем дату файла
    actionDate = str(extractFileDateTime(fileName))
    actionType, titanState = getActionProperty(text)
    if actionType == cUnknownObject:
        errorMessage = 'Не удалось определить тип события'
        return (textSource, errorMessage)
    if titanState:
        action['titanState'] = titanState

    if titanState == cTitanUnknown:
        log_text += 'titanState = TitanUnknown\n'
        print('titanState = TitanUnknown')

    aMembers = dict()

    # находим строки с данными [XX] <ник> <урон>
    text = '\n'.join(re.findall(r'\[\d.+\d', text))
    # удаляем номер рейтинга [XX]
    text = re.sub(r'^\[\d{,2}\]\s*', '', text, flags=re.MULTILINE)
    text = text.split('\n')

    resText = ''
    errorMessage = ''
    for i, sDate in enumerate(text, 1):
        # если ник начинается на цифру, обрабатываем конструкцию типа "[161400 УДАРОВ САЛОМ ПО 203"
        if sDate[0] == '[':
            sDate = sDate[len(str(i)) + 2:len(sDate)]
        nickName = re.sub(r'\s*\d+$', '', sDate)
        # пытаемся найти бойца в словаре
        nickNameOriginal = allianceMembers.get(nickName)
        nickNameSource = nickName
        if nickNameOriginal == None:
            # пытаемся найти бойца по подстроке в словаре
            fNick = findMembersInAlliance(sDate, allianceMembers)
            nickNameSource = fNick[0]
            nickNameOriginal = fNick[1]
            if nickNameOriginal == None:
                nickNameOriginal = nickName + ' Unknown Nick'
                errorMessage += f'NickName not found: {nickName}'
                unknownNicks.append(nickName)

        if nickNameSource != None:
            damage = sDate[len(nickNameSource): len(sDate)]
            try:
                aMembers[nickNameOriginal] = int(damage)
            except (ValueError):
                errorMessage = 'Недопустимое значение урона: ' + damage
                return (textSource, errorMessage)

            resText = resText + nickNameOriginal + ': ' + damage + '\n'
        else:
            errorMessage += f' NickName not found: {sDate}'
            unknownNicks.append(sDate)
            # print('not found: ' + sDate)

    action['members'] = aMembers
    data[actionType][actionDate] = action
    # если ошибок нет, то добавляем данные в файл
    if not errorMessage:
        with open('data.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False)

    return (textSource, errorMessage)


fileName = 'completed\\Screenshot_20200210-181017.jpg'
""".strftime('%Y%m%d-%H%M%S')"""
# print(str(extractFileDateTime(fileName)))
"""
Screenshot_20200302-224233.jpg      титан повержен
Screenshot_20200220-111510.jpg      война
Screenshot_20200213-111325.jpg      война
"""

unknownNicks = list()
log_text = ''

# загружаем данные о титанах и войнах
with open('data.json', "r", encoding='utf-8') as read_file:
    data = json.load(read_file)

# загружаем словарь бойцов из json
with open('AllianceMembers.json', 'r', encoding='utf-8') as fAllianceMembers:  # открываем файл на чтение
    allianceMembers = json.load(fAllianceMembers)  # загружаем из файла данные в словарь data

# загружаем config
with open('config.json', 'r', encoding='utf-8') as fconfig:  # открываем файл на чтение
    dconfig = json.load(fconfig)

# fn = 'Screenshot_20200213-111325.jpg'
fileslist = glob("screenshots\*.jpg") + glob("screenshots\*.txt")
# print('found files: ' + str(fileslist))
errorMessage = ''
for fn in fileslist:
    dBegin = DT.datetime.now()
    textSource, errorMessage = processingScreenshot(fn)
    if errorMessage != '':
        with open(fn[:fn.index('.')] + '.txt', 'w', encoding='utf-8') as error_file:
            print(textSource, file=error_file)
        print(errorMessage)
    else:
        try:
            os.rename(fn, 'completed\\' + fn[fn.index('\\') + 1:])
        except FileExistsError:
            os.remove(fn)
        # print(fn, 'completed\\'+fn[fn.index('\\')+1:])
    print(str(DT.datetime.now() - dBegin) + ' s.')
if unknownNicks:
    print('Unknown Nicks', unknownNicks)
print(errorMessage)
print(f'Титанов {len(data[cTitans])}: Войн {len(data[cWars])}')
with open('ProcessingScreenshots.log', 'a', encoding='utf-8') as log_file:
    print(str(DT.datetime.now()), file=log_file)
    print(log_text, file=log_file)
    if unknownNicks:
        print('Unknown Nicks', unknownNicks, file=log_file)
    if errorMessage != '':
        print(errorMessage, file=log_file)
    print(f'Титанов {len(data[cTitans])}: Войн {len(data[cWars])}', file=log_file)

os.system("pause")
