from flask import Flask, request, json
from flask_cors import CORS
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import os, sys
import configparser
from configparser import ConfigParser
import csv
import time

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
# http://127.0.0.0:8000/telegram?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s&user=Davier&group=TktPrueva&type=broadcast
# http://127.0.0.0:8000/cleandb?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s
# http://127.0.0.0:8000/updatebd?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s&user=5900098531
# postgres://telegrambot_tkt_user:7p2uqGFWiPARqzIyEsOcsqRv00C0g50e@dpg-ck68gl5drqvc73bj9kpg-a.oregon-postgres.render.com/telegrambot_tkt
# gunicorn --bind 0.0.0.0:8000 app:app

app = Flask(__name__)
CORS(app)
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
    await client.disconnect()

    returndata = ""

    if(userdata):
        valid = validUserFromDb(userdata)
        print("validando desde bd %s"%valid)
        if(valid):
            returndata = {'response': 'user_ok', 'data': userdata}
        else:
            returndata = {'response': 'user_exist'}
    else:
        returndata = {'response': "user_not_registry"}
    
    response = app.response_class(
        response=json.dumps(returndata),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/telegram', methods=["POST"])
async def telegram():
    data = request.get_json()
    user = data["username"]
    token = data["token"]
    group = data["group"]
    type = data["type"]
    print(token+" "+user+" "+group+" "+type)

    if(_TOKEN_ != token):
        return "invalid Token"
    
    #client = await startConnection()
    #asyncio.run()
    client = await startConnection()
    userdata = await validateUsername(client, group, type, user)
    await client.disconnected

    returndata = ""

    if(userdata):
        valid = validUserFromDb(userdata)
        print("validando desde bd %s"%valid)
        if(valid):
            returndata = {'response': 'user_ok', 'data': userdata}
        else:
            returndata = {'response': 'user_exist'}
    else:
        returndata = {'response': "user_not_registry"}
    
    response = app.response_class(
        response=json.dumps(returndata),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/cleandb', methods=["GET"])
def cleandb():
    token = request.args.get('token')

    if(_TOKEN_ != token):
        return "invalid Token"
    
    returndata = ""

    try:
        conexion = None
        params = config()
        #print(params)

        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        
        # creación del cursor
        cur = conexion.cursor()
        cur.execute("DROP TABLE IF EXISTS telegram")
        conexion.commit()
        print("se elimino la tabla correctamente")
        conexion.close()
        returndata = {'response': 'clean_bd_ok'}
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        returndata = {'response': 'clean_bd_ok', 'data': error}
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

    response = app.response_class(
        response=json.dumps(returndata),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/updatebd', methods=["GET"])
def updatebd():
    token = request.args.get('token')
    user = request.args.get('user')
    value = request.args.get('value')
    if(_TOKEN_ != token):
        return "invalid Token"
    if(user == None or user == ""):
        return "invalid User"
    
    if(value == None):
        value = 0

    returndata = ""

    try:
        conexion = None
        params = config()
        #print(params)

        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        
        # creación del cursor
        cur = conexion.cursor()
        sql = "UPDATE telegram SET valid=1 WHERE userid=%s;"
        cur.execute(sql, (user,))
        print("actualizando la base de datos")
        conexion.commit()
        cur.execute( "SELECT userid, valid FROM telegram" )

        # Recorremos los resultados y los mostramos

        userlist = cur.fetchall()
        for userid, valid in userlist :
            print("revisando la lista de los usuarios: %s valid: %s"%(userid, valid))
        # Cierre de la comunicación con PostgreSQL
        conexion.close()
        print("se cerro la conexion con la base de datos")
        returndata = {'response': 'user_updated_ok'}

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        returndata = {'response': 'user_updated_error', 'data': error}
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

    response = app.response_class(
        response=json.dumps(returndata),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/getusers', methods=["GET"])
def getusers():
    token = request.args.get('token')
    user = request.args.get('user')
    if(_TOKEN_ != token):
        return "invalid Token"
    if(user == None or user == ""):
        return "invalid User"
    
    try:
        conexion = None
        params = config()
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        
        cur = conexion.cursor()
        cur.execute( "SELECT userid, valid FROM telegram" )
        ListUser = []
        userlist = cur.fetchall()
        for userid, valid in userlist :
            ListUser.append([userid, valid])
            print("revisando la lista de los usuarios: %s valid: %s"%(userid, valid))
        conexion.close()
        print("se cerro la conexion con la base de datos")
        return {'response': 'user_list_ok', 'data': ListUser}

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {'response': 'user_updated_error', 'data': error}
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

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
                    print("el chat es %s"% chat.title)
                    groups.append(chat)
            
            elif chat.megagroup == True or chat.gigagroup == True:
                groups.append(chat)
        except:
            continue

    i=0
    for g in groups:
        
        if(g.username.lower() == _group.lower()):
            print("el grupo es %s"%g.title)
            target_group = groups[int(i)]
            break
        i+=1
    print("el target grup es %s" % target_group.title)
    all_participants = []
    userdata = False
    all_participants = await client.get_participants(target_group, aggressive=True)
    for user in all_participants:
        if user.first_name:
            first_name= user.first_name
        else:
            first_name= ""
        if user.last_name:
            last_name= user.last_name
            print("el last_name es %s "%last_name)
        else:
            last_name= ""
        name= (first_name + ' ' + last_name).strip()
        print("los usuarios son iguales %s %s name %s" % (user.username, _user, name))
        if name == _user:
            
            userdata = {
                'username' : user.username,
                'name': name,
                'id' : user.id,
                'hash': user.access_hash
            }
            break
    return userdata

def validUserFromDb(data):
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

        cur.execute( "SELECT userid, valid FROM telegram" )

        # Recorremos los resultados y los mostramos

        userlist = cur.fetchall()
        for userid, valid in userlist :
            #print("el user id %s el valid %s"%(userid, valid))
            if(userid == data['id'] and valid == 0):
                print("el usuario %s esta regisrado en el canal pero no ha recibido los token"% data['name'])
                conexion.close()
                return True
            
            elif(userid == data['id'] and valid == 1):
                print("el usuario %s ya recibio los token"% data['name'])
                conexion.close()
                return False
            else:
                print("ingresando un nuevo usuario %s"% data['name'])
                sql="insert into telegram(userid, valid) values (%s, 0)"
                datos=(data['id'],)
                cur.execute(sql, datos)
                conexion.commit()
                conexion.close()
                return True
        
        print("ingresando un nuevo usuario final %s"% data['name'])
        sql="insert into telegram(userid, valid) values (%s, 0)"
        datos=(data['id'],)
        cur.execute(sql, datos)
        conexion.commit()
        conexion.close()
        return True
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def config(archivo='config.ini', seccion='postgresql'):
    # Crear el parser y leer el archivo
    parser = ConfigParser()
    parser.read(archivo)
    print('se ejecuto config')
 
    # Obtener la sección de conexión a la base de datos
    db = {}
    if parser.has_section(seccion):
        params = parser.items(seccion)
        for param in params:
            db[param[0]] = param[1]
        return db
    else:
        raise Exception('Secccion {0} no encontrada en el archivo {1}'.format(seccion, archivo))
 
if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)
