from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from configparser import ConfigParser
import configparser
import os, sys
import psycopg2
import hashlib
import uuid
from datetime import datetime
import random
from functools import reduce
import time

_DEFAULTOKENS_ = 30
_DEFAULTTOKENREF_ = 5
_MINREF_ = 3

re="\033[1;31m"
gr="\033[1;32m"
cy="\033[1;36m"

last_date = None
chunk_size = 200

chats = []
groups=[]

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
        
        if(g.username.lower() == _group.lower()):
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
        else:
            last_name= ""
        name= (first_name + ' ' + last_name).strip()
        
        print("usuario: %s busqueda: %s" % (user.username, _user))
        if user.username == _user:
            userdata = {
                'username' : user.username,
                'name': name,
                'id' : user.id,
                'hash': user.access_hash
            }
            break
    return userdata

def validUserFromDb(data, hash):
    try:
        conexion = None
        #params = config()
        params = config('localdb')
        #print(params)
    
        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        
        # creando la tabla si no existe
        cur.execute("CREATE TABLE IF NOT EXISTS telegram (id serial not null, userid bigint not null, valid smallint not null, mhash varchar not null, primary key (id))")
        #cur.execute("CREATE INDEX userids ON telegram (userid)")

        cur.execute( "SELECT valid FROM telegram where userid=%s and mhash=%s", (data['id'], hash) )

        # Recorremos los resultados y los mostramos

        userlist = cur.fetchall()
        for valid in userlist :
            #print("el user id %s el valid %s"%(userid, valid))
            if(valid == 0):
                print("el usuario %s esta regisrado en el canal pero no ha recibido los token "% data['id'])
                conexion.close()
                return True
            
            elif(valid == 1):
                print("el usuario %s ya recibio los token"% data['id'])
                conexion.close()
                return False
            else:
                print("ingresando un nuevo usuario %s"% data['id'])
                sql="insert into telegram(userid, valid, mhash) values (%s, 0, %s)"
                datos=(data['id'], hash)
                cur.execute(sql, datos)
                conexion.commit()
                conexion.close()
                return True
        
        print("ingresando un nuevo usuario final %s"% data['id'])
        sql="insert into telegram(userid, valid, mhash) values (%s, 0, %s)"
        datos=(data['id'], hash)
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

def config(seccion='postgresql', archivo='config.ini'):
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

def storeTwitter(id, user, follow, shash):
    try:
        conexion = None
        #params = config()
        params = config('localdb')
        #print(params)
    
        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        isexist = False
        cur.execute( "SELECT userid, username, follow, mhash, valid FROM twitter where userid=%s and mhash = shash", (id, shash) )
        userlist = cur.fetchall()
        for data in userlist:
            print(data[0])
            if(data[0] == id):
                isexist = True
            
        if(isexist):
            return "user_exist"
        # creando la tabla si no existe
        cur.execute("CREATE TABLE IF NOT EXISTS twitter (id serial not null, userid bigint not null, username varchar not null, follow varchar not null, mhash varchar not null, primary key (id))")
        #cur.execute("CREATE INDEX userids ON telegram (userid)")
        sql="insert into twitter(userid, username, follow, mhash, valid) values (%s, %s, %s, %s, 0)"
        datos=(id, user, follow, hash)
        cur.execute(sql, datos)
        conexion.commit()
        conexion.close()
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def validateTwitterTelegram(twitter, telegram):
    try:
        conexion = None
        #params = config()
        params = config('localdb')
        #print(params)
    
        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()

        twittervalid = False
        twitterexist = False
        cur.execute( "SELECT valid FROM twitter where mhash=%s", (twitter,) )
        userlist = cur.fetchall()
        for valid in userlist :
            twitterexist = True
            if(valid == 0):
                twittervalid = True
            elif(valid == 1):
                twittervalid = False
        

        ################################ TELEGRAM #################################
        
        # creación del cursor
        #cur = conexion.cursor()
        
        # creando la tabla si no existe
        
        cur.execute( "SELECT valid FROM telegram where mhash=%s", (hash,) )

        # Recorremos los resultados y los mostramos

        userlist = cur.fetchall()

        telegramvalid = False
        telegramexist = False
        for valid in userlist :
            telegramexist = True
            if(valid == 0):
                telegramvalid = True
            elif(valid == 1):
                telegramvalid = False

        return {"twitterexist": twitterexist, "twittervalid": twittervalid, "telegramexist": telegramexist, "telegramvalid": telegramvalid}
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def validateWallet(wallet, referido):
    try:
        redif = "%s%s"%(uuid.uuid4().hex, uuid.uuid4().hex)
        conexion = None
        #params = config()
        params = config('localdb')
        #print(params)
    
        # Conexion al servidor de PostgreSQL
        print('Conectando a la base de datos PostgreSQL...')
        conexion = psycopg2.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        isexist = False
        cur.execute("CREATE TABLE IF NOT EXISTS metamask (id serial not null, refid varchar not null, wallet varchar not null, tokens bigint not null, referidos bigint not null, refpaid bigint not null, paid smallint not null, primary key (id))")
        #cur.execute("CREATE INDEX userids ON telegram (userid)")
        conexion.commit()

        cur.execute( "SELECT paid FROM metamask where wallet= %s", (wallet,) )

        # Recorremos los resultados y los mostramos
        returndata = ""
        walletlist = cur.fetchall()
        for paid in walletlist :
            #print("el user id %s el valid %s"%(userid, valid))
            if(paid == 0):
                print("wallet %s finished the process but has not received the tokens" % wallet)
                return ('notpaid', "wallet %s finished the process but has not received the tokens" % wallet)
            elif(paid == 1):
                print("wallet %s has received the tokens" % wallet)
                return ('paid', "wallet %s has received the tokens" % wallet)
        
        print("ingresando una nueva wallet %s" % wallet)
        sql="insert into metamask(refid, wallet, tokens, referidos, refpaid, paid) values (%s, %s, %s, 0, 0, 0)"
        datos=(redif, wallet, _DEFAULTOKENS_)
        cur.execute(sql, datos)
        conexion.commit()

        cur.execute( "SELECT referidos FROM metamask where refid= %s", (referido,) )
        reflist = cur.fetchone()
        if(reflist):
            sql = "UPDATE metamask SET referidos=%s WHERE refid=%s;"
            newref = int(reflist) + 1
            data = (newref, referido)
            cur.execute(sql, data)
            conexion.commit()
        conexion.close()
        print("se actualizo los referidos id %s " % referido)
        return ("ok", "otra cosa", redif)
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def calculate_sha256(data):
    password = "ecfbeb0a78c04e5.*692a4*..e5c___69..0f9c*f1f**0cdae__f723e6346f2b8af187$@7f21d4b4$$3a0b33c1.__26afd40a$$3b**.125ce8a$$457.*b0bba"

    data = "%s %s"%(data, password)
    if isinstance(data, str):
        data = data.encode()
    md5hash = hashlib.md5(data).hexdigest().encode()
    sha256_hash = hashlib.sha256(md5hash).hexdigest()
    
    return sha256_hash

def authCode():
    numeros = map(lambda x: random.randint(1, 9), range(6))
    return reduce(lambda x, y: str(x) + str(y), numeros)

def timestamp():
    fecha = "%s" % datetime.now()
    timeret = time.mktime(datetime.strptime(fecha[:19], "%Y-%m-%d %H:%M:%S").timetuple())
    return timeret