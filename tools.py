import requests
from faker import Faker
import config
import sqlite3
import time
import json
from python_rucaptcha import ImageCaptcha
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'X-Requested-With' : 'XMLHttpRequest'
}

class Yandex:

    def __init__(self):

        self.session = requests.session()
        self.session.headers = headers

    def getValues(self):

        try:
            r = self.session.get('https://passport.yandex.ru/registration/')

            bs = BeautifulSoup(r.text, 'lxml')
            tmp = str(bs.find('script', {'id' : "storeScript"}))

            self.csrf_track = tmp.split('"csrf":"')[1].split('"')[0]

            self.track_id = r.text.split('"registerTrackId":"')[1].split('"')[0]
            return True

        except Exception as e:
            dataBase().log(f'ERROR > Line 39 tools.py > {e}')
            return False

    def generateCaptchaUrl(self):

        try:

            js = self.session.post(
                'https://passport.yandex.ru/registration-validations/textcaptcha',
                data = {
                    'track_id' : self.track_id,
                    'csrf_token' : self.csrf_track,
                    'ocr' : 'true',
                    'language' : 'ru'
                }
            ).text
            return json.loads(js)['image_url']

        
        except Exception as e:
            dataBase().log(f'ERROR > Line 59 tools.py > {e}')

    def getCaptchaSolve(self, url : any):

        try:

            user_answer = ImageCaptcha.ImageCaptcha(rucaptcha_key=config.apiKey).captcha_handler(captcha_link=url)

            self.answer = user_answer['captchaSolve']
            return self.answer
        
        except Exception as e:
            dataBase().log(f'ERROR > Line 71 tools.py > {e}')

    def generateData(self):

        try:

            if config.lang == 'ru':
                f = Faker('ru_RU')
            else:
                f = Faker('en_US')

            self.name = f.first_name()
            self.last_name = f.last_name()
            self.login = 'A' + f.md5()[:12]
            self.password = f.md5()[:15]

            data = {
                'track_id' : self.track_id,
                'csrf_token' : self.csrf_track,
                'firstname' : self.name,
                'lastname' : self.last_name,
                'surname'  : '',
                'login'    : self.login,
                'password' : self.password,
                'password_confirm' : self.password,
                'hint_question_id' : '12',
                'hint_question' : 'Фамилия вашего любимого музыканта',
                'hint_question_custom' : '',
                'hint_answer' : 'test',
                'captcha' : self.answer,
                'phone' : '',
                'phoneCode' : '',
                'publicId' : '',
                'human-confirmation' : 'captcha',
                'eula_accepted' : 'on',
                'type' : 'alternative'
            }

            return data
        
        except Exception as e:
            dataBase().log(f'ERROR > Line 112 tools.py > {e}')
            return dict()

    def sendCaptcha(self):

        self.session.headers['X-Requested-With'] = 'XMLHttpRequest'
        r = self.session.post('https://passport.yandex.ru/registration-validations/checkHuman',
        data = {
            'track_id' : self.track_id,
            'csrf_token' : self.csrf_track,
            'answer' : self.answer
        })
        return json.loads(r.text)

    def sendRegPacket(self, data):

        r = self.session.post(
            'https://passport.yandex.ru/registration-validations/registration-alternative',
            data=  data
        )
        return json.loads(r.text)

class dataBase:
    def __init__(self, databaseFile = 'main.db'):
        self.conn = sqlite3.connect(databaseFile,check_same_thread=False)
        self.database = self.conn.cursor()

    def getAllDb(self, tableName : str) -> list:
        self.database.execute(f"SELECT * from \"{tableName}\"")
        self.conn.commit()
        return self.database.fetchall()

    def addUser(self, id : any) -> None:

        
        self.database.execute(f'DELETE from users where id = ?', (str(id), ))
        self.database.execute(
            f"INSERT INTO \"users\"('id', 'stat') VALUES(?, ?)", 
            (str(id), 'False')
        )
        
        self.conn.commit()
    def verifUser(self, id : any):
        self.database.execute(f'DELETE from users where id = ?', (str(id), ))
        self.database.execute(
            f"INSERT INTO \"users\"('id', 'stat') VALUES(?, ?)", 
            (str(id), 'True')
        )
        
        self.conn.commit()

    def checkUser(self, id : any) -> bool:

        for i in self.getAllDb('users'):
            if i[0] == str(id) and i[1] == 'True':

                return True

        return False

    def userInDatabase(self, id : any) -> bool:

        for i in self.getAllDb('users'):
            if i[0] == str(id):

                return True

        return False
    
    def log(self, text : str):

        Time = int(time.time())

        self.database.execute(
            f"INSERT INTO \"logs\"('time', 'text') VALUES(?, ?)", 
            (str(Time), str(text))
        )
        self.database.execute(
            f"INSERT INTO \"tmpLogs\"('time', 'text') VALUES(?, ?)", 
            (str(Time), str(text))
        )
        
        self.conn.commit()

    def deleteTempLogs(self):
        self.database.execute(
            'DELETE FROM tmpLogs'
        )
        self.conn.commit()

    def addAccount(self, login : str, password : str):

        self.database.execute(
            f"INSERT INTO \"accounts\"('login', 'password') VALUES(?, ?)", 
            (str(login), str(password))
        )
        self.conn.commit()


    def getAccountsCount(self) -> int:

        return len(self.getAllDb('accounts'))


