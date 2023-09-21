from flask import Flask, request
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import os, sys
import configparser
import csv
import time
from config import config
import psycopg2

_TOKEN_ = 'tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s'
chats = []
last_date = None
chunk_size = 200
groups=[]

re="\033[1;31m"
gr="\033[1;32m"
cy="\033[1;36m"


cpass = configparser.RawConfigParser()
cpass.read('config.data')

try:
    api_id = cpass['cred']['id']
    api_hash = cpass['cred']['hash']
    phone = cpass['cred']['phone']
    client = TelegramClient(phone, api_id, api_hash)
except KeyError:
    os.system('clear')
    print(re+"[!] run python3 setup.py first !!\n")
    sys.exit(1)

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    os.system('clear')
    client.sign_in(phone, input(gr+'[+] Enter the code: '+re))

app = Flask(__name__)

@app.route('/telegram', methods=["POST", "GET"])
def telegram():
    data = request.get_json()
    user = data["username"]
    token = data["token"]
    group = data["group"]
    type = data["type"]

    if(_TOKEN_ != token):
        return "invalid Token"
    
    userdata = validateUsername(group, type, user)
    if(userdata):
        if(validUserFromDb(userdata)):
            return {'response': 'user_ok'}
        else:
            return {'response': 'user_exist'}
    else:
        return {'response': "user_not_registry"}

def validateUsername(_group, _type, _user):
    result = client(GetDialogsRequest(
             offset_date=last_date,
             offset_id=0,
             offset_peer=InputPeerEmpty(),
             limit=chunk_size,
             hash = 0
         ))
    chats.extend(result.chats)
    for chat in chats:
        try:
            if(_type == "broadcast"):
                if chat.broadcast == True:
                    groups.append(chat)
            
            elif chat.megagroup == True or chat.gigagroup == True:
                groups.append(chat)
        except:
            continue

    i=0
    for g in groups:
        if(g.title == _group):
            target_group = groups[int(i)]
            break
        i+=1
    all_participants = []
    userdata = False
    all_participants = client.get_participants(target_group, aggressive=True)
    for user in all_participants:
        if user.username == _user:
            userdata = {
                'username' : user.username,
                'id' : user.id,
                'hash': user.access_hash
            }
            break
    return userdata

def validUserFromDb(data):
    conexion = None
    try:
        # Lectura de los parámetros de conexion
        params = config()
 
        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
 
        # creación del cursor
        cur = conexion.cursor()
        
        # creando la tabla si no existe
        print('La version de PostgreSQL es la:')
        cur.execute('CREATE TABLE `telegrambot_tkt`.`telegram` (`id` BIGINT(255) NOT NULL AUTO_INCREMENT , `userid` BIGINT(255) NOT NULL, PRIMARY KEY (`id`), INDEX (`id`, `userid`)) ENGINE = InnoDB;')
 
        cur.execute( "SELECT userid FROM telegram" )

        # Recorremos los resultados y los mostramos
        for userid in cur.fetchall() :
            if(userid == data.id):
                return False

        sql="insert into telegram(userid) values (%s)"
        datos=(data.id)
        cur.execute(sql, datos)
       
        # Cierre de la comunicación con PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

