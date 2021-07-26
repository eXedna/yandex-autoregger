from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import *
from aiogram.types.base import Boolean
import config
import os
from faker import Faker
from time import sleep
from threading import Thread
import asyncio
import time
import json
import tools
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup

#---------- global vars ----------#

global db
db = tools.dataBase()

global threadsLst
threadsLst = []

global threadsCount
threadsCount = 5

global logLst
logLst = []

global boolRun
boolRun = False

global mainKb
mainKb = InlineKeyboardMarkup()
# InlineKeyboardButton(text = '', callback_data=json.dumps({'act' : ''}))
mainKb.add(
    InlineKeyboardButton(text = 'Старт', callback_data=json.dumps({'act' : 'startReg'})),
    InlineKeyboardButton(text = 'Стоп', callback_data=json.dumps({'act' : 'stopReg'}))
)
mainKb.add(
    InlineKeyboardButton(text = 'Статистика', callback_data=json.dumps({'act' : 'getStat'})),
    InlineKeyboardButton(text = 'Аккаунты', callback_data=json.dumps({'act' : 'getAccounts'}))
)
mainKb.add(
    InlineKeyboardButton(text = 'Логи', callback_data=json.dumps({'act' : 'getLogs'})),
    InlineKeyboardButton(text = 'Полные логи', callback_data=json.dumps({'act' : 'getAllLogs'}))
)
mainKb.add(InlineKeyboardButton(text = 'Изменить кол-во потоков', callback_data=json.dumps({'act' : 'setThreads'})))

#---------------------------------#

#---------------------------------------------------------------- main func ----------------------------------------------------------------#
def main():
    def dada():
        yandex = tools.Yandex()
        t = yandex.getValues()
        if not t:
            return
        logLst.append(f'Получил csrf_token')
        url = yandex.generateCaptchaUrl()
        logLst.append(f'Получил ссылку на капчу: {url}')
        ans = yandex.getCaptchaSolve(url)
        logLst.append(f'Поймал решение капчи: {ans}')
        r = yandex.sendCaptcha()
        if r['status'] == 'ok':
            logLst.append(f'Съел капчу')
        else:
            logLst.append(f'ERROR > Какая-то ошибка: {r}')
            return

        data = yandex.generateData()
        

        r = yandex.sendRegPacket(data)
        if r['status'] == 'ok':
            db.addAccount(data['login'], data['password'])
            sleep(.01)
            logLst.append(f'Аккаунт создан. Данные для входа ниже\n{"-" * 20}\nЛогин: {data["login"]}\nПароль: {data["password"]}\n{"-" * 20}\n')
                
        else:
            logLst.append(f'ERROR > main() bot.py > Какая-то ошибка: {r}')

    while True:
        global boolRun
        if boolRun:
  
            while len(threadsLst) == 5:
                for i in threadsLst:
                    if not i.is_alive():
                        threadsLst.remove(i) 
                sleep(0.5)   
            
            t = Thread(target=dada)
            threadsLst.append(t)
            t.start()
            sleep(0.5)
        sleep(0.1)


Thread(target=main).start()

def Log():
    while True:
        for i in logLst:
            db.log(i)
            logLst.remove(i)
        sleep(0.1)

Thread(target = Log).start()

#-------------------------------------------------------------------------------------------------------------------------------------------#

storage = MemoryStorage()
bot = Bot(token=config.botToken)
dp = Dispatcher(bot, storage=storage)

@dp.message_handler(state = 'getThreads')
async def setThreads1(message):

    id = message.chat.id
    text= message.text

    state = dp.current_state(user=id)
    await state.reset_state()

    try:
        text = int(text)

    except:
        await bot.send_message(id, f'Похожу ты отправил не число...', reply_markup=mainKb)
    global threadsCount
    threadsCount = text
    await bot.send_message(id, f'Кол-во потоков теперь: {threadsCount}', reply_markup=mainKb)

@dp.message_handler(commands=['start'])
async def startMess(message):

    text = message.text
    id = message.chat.id

    if not db.userInDatabase(id):
        db.addUser(id)
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(text = 'Одобрить', callback_data=json.dumps({'act' : 'verifUser', 'id' : id})),InlineKeyboardButton(text = 'Пофиг', callback_data=json.dumps({'act' : 'delete'})))
        
        await bot.send_message(config.admin, f'Новый запрос на верификацию\n{"━" * 23}\n\nID: {id}\nИмя: {message.chat.first_name}\nUsername: @{message.chat.username}', reply_markup=kb)
        return

    if db.checkUser(id):

        await bot.send_message(id, f'Привет, {message.chat.first_name}!\nДанный бот нужен для удобной работы с автореггером yandex аккаунтов', reply_markup=mainKb)



@dp.callback_query_handler(lambda message:True)
async def ans(message):
    dictInfo = json.loads(message.data)
    id = message.message.chat.id
    global boolRun

    act = dictInfo['act']

    if act == 'verifUser':

        tgId = dictInfo['id']
        db.verifUser(tgId)
        await bot.delete_message(id ,message.message.message_id)
        await bot.send_message(id, f'Пользователь теперь может работать с ботом', reply_markup=mainKb)
        await bot.send_message(tgId, f'Админ разрешил пользоваться вам ботом')

    if act == 'delete':
        await bot.delete_message(id ,message.message.message_id)

    if act == 'startReg':

        boolRun = True
        db.deleteTempLogs()
        await bot.delete_message(id ,message.message.message_id)
        await bot.send_message(id, f'Авторегистрация запущена', reply_markup=mainKb)

    if act == 'stopReg':

        boolRun = False
        await bot.delete_message(id ,message.message.message_id)
        await bot.send_message(id, f'Авторегистрация оставлена', reply_markup=mainKb)
    
    if act == 'getAllLogs':

        data = db.getAllDb('logs')
        txt = f'Логи бота (регистрация аккантов)\n\n\n'
        for i in data:

            Time = time.localtime(int(i[0]))
            now = f'{Time.tm_year}-{Time.tm_mon}-{Time.tm_mday} {Time.tm_hour}:{Time.tm_min}:{Time.tm_sec}'
            txt += f'[{now}] -> {i[1]}\n'

        fName = Faker().md5()[:5] + '.txt'
        with open(fName, 'w') as f:
            f.write(txt)
        await bot.delete_message(id ,message.message.message_id)        
        await bot.send_document(id, ('logs.txt', open(fName, 'rb')), caption='Логи бота', reply_markup=mainKb)
        os.remove(fName)
    if act == 'getLogs':

        data = db.getAllDb('tmpLogs')
        txt = f'Логи бота за сессию (регистрация аккантов)\n\n\n'
        for i in data:

            Time = time.localtime(int(i[0]))
            now = f'{Time.tm_year}-{Time.tm_mon}-{Time.tm_mday} {Time.tm_hour}:{Time.tm_min}:{Time.tm_sec}'
            txt += f'[{now}] -> {i[1]}\n'

        fName = Faker().md5()[:5] + '.txt'
        with open(fName, 'w') as f:
            f.write(txt)
        await bot.delete_message(id ,message.message.message_id)        
        await bot.send_document(id, ('logs.txt', open(fName, 'rb')), caption='Логи бота за сессию', reply_markup=mainKb)
        os.remove(fName)


    if act == 'getAccounts':

        data = db.getAllDb('accounts')
        txt = ''
        for i in data:

            txt += f'{i[0]}:{i[1]}\n'
        txt = txt[:-1]

        fName = Faker().md5()[:5] + '.txt'
        with open(fName, 'w') as f:
            f.write(txt)
        await bot.delete_message(id ,message.message.message_id)        
        await bot.send_document(id, ('accounts.txt', open(fName, 'rb')), caption='Аккаунты идут в виде логин:пароль', reply_markup=mainKb)
        os.remove(fName)

    if act == 'getStat':

        if boolRun:
            stat = 'работает'
        else:
            stat = 'выключена'

        txt = f'Бот работает.\n\nАвторегистрация: {stat}\nАккантов зарегестрировано: {db.getAccountsCount()}\nПотоков: {threadsCount}'
        await bot.delete_message(id ,message.message.message_id)        
        await bot.send_message(id, txt, reply_markup=mainKb)
    
    if act == 'setThreads':

        await bot.delete_message(id ,message.message.message_id)   
        state = dp.current_state(user=id)
        await state.set_state('getThreads')
        await bot.send_message(id, f'Отправь мне количество потоков')

    

loop = asyncio.get_event_loop()
executor.start_polling(dp,loop=loop, skip_updates=True)
