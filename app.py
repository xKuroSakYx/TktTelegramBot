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
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

_TOKEN_ = 'tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s'
chats = []
last_date = None
chunk_size = 200
groups=[]

re="\033[1;31m"
gr="\033[1;32m"
cy="\033[1;36m"

# http://127.0.0.1:8000/telegram?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s&user=kalguanchez&group=thekeyoftrueTKT&type=broadcast
# gunicorn --bind 0.0.0.0:8000 app:app

app = Flask(__name__)
@app.route('/telegram', methods=["GET"])
async def telegramget():
    token = request.args.get('token')
    user = request.args.get('user')
    group = request.args.get('group')
    type = request.args.get('type')
    print(token+" "+user+" "+group+" "+type)

    if(_TOKEN_ != token):
        return "invalid Token"
    
    #client = await startConnection()
    #asyncio.run()
    client = await startConnection()
    userdata = await validateUsername(client, group, type, user)
    if(userdata):
        if(validUserFromDb(userdata)):
            return {'response': 'user_ok'}
        else:
            return {'response': 'user_exist'}
    else:
        return {'response': "user_not_registry"}

@app.route('/telegram', methods=["POST"])
async def telegram():
    data = request.get_json()
    user = data["username"]
    token = data["token"]
    group = data["group"]
    type = data["type"]

    if(_TOKEN_ != token):
        return "invalid Token"
    
    #client = await startConnection()
    validateUsername(group, type, user)

async def startConnection():
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

    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        #os.system('clear')
        await client.sign_in(phone, input(gr+'[+] Enter the code: '+re))
    return client

async def validateUsername(client, _group, _type, _user):
    result = await client(GetDialogsRequest(
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
        
        if(g.username == _group):
            print("el grupo es "+g.title)
            target_group = groups[int(i)]
            break
        i+=1
    all_participants = []
    userdata = False
    all_participants = await client.get_participants(target_group, aggressive=True)
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
        conexion = None
        params = config()
        #print(params)
    
        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        
        # creación del cursor
        cur = conexion.cursor()
        
        # creando la tabla si no existe
        cur.execute("CREATE TABLE IF NOT EXISTS telegram (id serial not null, userid bigint not null, valid smallint not null, primary key (id))")
        #cur.execute("CREATE INDEX userids ON telegram (userid)")

        cur.execute( "SELECT userid FROM telegram" )

        # Recorremos los resultados y los mostramos
        isexist = False
        userlist = cur.fetchall()
        for userid in userlist :
            if(userid[0] == data['id']):
                isexist = True
                break
        if(isexist):
            return False
        else:
            sql="insert into telegram(userid) values (%s)"
            datos=(data['id'],)
            cur.execute(sql, datos)
            conexion.commit()
            conexion.close()
        #cur.execute("DELETE * FROM telegram")
        #conexion.commit()
        # Cierre de la comunicación con PostgreSQL
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)
