import re
from typing import List, Any, Union

cTitanKilled = 'TitanKilled'
cSortTotalPoint = 0
cSortAvgPoint = 1
cFillChar = '█'
cBarLength = 22

def statSummary(data, typeObject, regExpMask, sort=cSortTotalPoint):
    res = ''
    statRes = dict()
    membersCount = dict()
    actions = data[typeObject]

    keys = list(data[typeObject].keys())
    # фильтруем ключи по маске
    keyList = list(filter(lambda x: bool(re.search(regExpMask, x)), keys))
    keyList.sort()
    print(keyList)

    titanKilledCount = 0
    for objectDate in keyList:
        titanState = actions[objectDate].get('titanState')
        titanKilled = False
        if titanState is not None:
            if titanState == cTitanKilled:
                titanKilled = True
                titanKilledCount += 1
        if titanKilled | (typeObject == 'wars'):
            for member in actions[objectDate]['members'].items():
                statRes[member[0]] = (statRes.get(member[0]) if statRes.get(member[0]) is not None else 0) + member[1]
                # счетчик объектов, в которых участвовал боец
                membersCount[member[0]] = 1 if membersCount.get(member[0]) is None else membersCount[member[0]] + 1

    sortRes = list(statRes.items())
    for i in enumerate(sortRes):
        sortRes[i[0]] = list(sortRes[i[0]])
        sortRes[i[0]].append(int(i[1][1]/membersCount[i[1][0]]))

    if sort == cSortTotalPoint:
        sortRes.sort(key=lambda i: i[1], reverse=True)
        targetColumn = 1
    elif sort == cSortAvgPoint:
        sortRes.sort(key=lambda i: i[2], reverse=True)
        targetColumn = 2

    maxDamage = sortRes[0][targetColumn]
    res = f'За {regExpMask} ' if regExpMask != '' else ''
    if typeObject == 'titans':
        res += f"убито {titanKilledCount} #титанов из {len(keyList)}\nСуммарный и (средний) урон по убитым титанам\n"
    elif typeObject == 'wars':
        res += f"проведено #войн: {len(keyList)}\nСуммарное и (среднее) к-во очков по войнам\n"


    res += f'\n'.join(
        f"[{e[0] + 1}] {e[1][0]}: {e[1][1]} ({e[1][2]})\n{cFillChar * int(e[1][targetColumn] * cBarLength / maxDamage)} "
        f"{e[1][targetColumn] / maxDamage * 100:.1f}%" for e in enumerate(sortRes))
    return res


# # загружаем данные о титанах и войнах
# with open('data.json', "r", encoding='utf-8') as fdata:
#     data = json.load(fdata)
#
# # загружаем словарь бойцов из json
# with open('AllianceMembers.json', 'r', encoding='utf-8') as fAllianceMembers:  # открываем файл на чтение
#     allianceMembers = json.load(fAllianceMembers)  # загружаем из файла данные в словарь data
#
# mask = '2020-03'
#
# res = statSummary(data, 'titans', mask, cSortAvgDamage)
# print(res)
#'2020-02-10 18:10:17', '2020-02-11 10:57:48', '2020-02-14 10:27:05', '2020-02-15 10:48:35',
#'2020-02-25 07:32:10', '2020-03-01 11:14:33', '2020-03-01 22:29:11', '2020-03-02 22:42:33',
#'2020-03-04 19:53:46', '2020-03-05 21:22:30', '2020-03-06 21:28:52', '2020-03-07 12:31:23',
#'2020-03-09 18:34:59', '2020-03-10 12:40:56', '2020-03-14 10:36:12']

# a = ['2020-02-10 18:10:17', '2020-02-11 10:57:48', '2020-02-14 10:27:05', '2020-02-15 10:48:35', '2020-02-25 07:32:10', '2020-03-01 11:14:33', '2020-03-01 22:29:11', '2020-03-02 22:42:33', '2020-03-04 19:53:46', '2020-03-05 21:22:30', '2020-03-06 21:28:52', '2020-03-07 12:31:23', '2020-03-09 18:34:59', '2020-03-10 12:40:56', '2020-03-14 10:36:12']
# aList = list(filter(lambda x: bool(re.search('2020-0[23]-1[0-6]', x)), a))
# print(aList)
