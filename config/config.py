from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from configparser import ConfigParser
import configparser
import os, sys, csv
#import psycopg2
import mysql.connector
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
        tktid = authCode(15)
        conexion = None
        #params = config()
        params = config('x6nge')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql...validateUsername')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        
        # creando la tabla si no existe
        #tktid bigint(255) not null,
        cur.execute("CREATE TABLE IF NOT EXISTS telegram (id bigint(255) not null AUTO_INCREMENT, userid bigint(255) not null, valid int(1) not null, mhash varchar(255) not null, primary key (id))  ENGINE = InnoDB")
        #cur.execute("CREATE INDEX userids ON telegram (userid)")

        cur.execute( "SELECT valid, mhash FROM telegram where userid=%s", (data['id'], ) )

        # Recorremos los resultados y los mostramos

        userlist = cur.fetchall()
        for valid in userlist :
            #print("el user id %s el valid %s"%(userid, valid))
            if(valid[0] == 0 and valid[1] == hash):
                print("el usuario %s esta regisrado en el canal pero no ha recibido los token "% data['id'])
                conexion.close()
                #return {'valid': True, 'tktid': valid[1]}
                return True
            
            elif(valid[0] == 1 and valid[1] == hash):
                print("el usuario %s ya recibio los token"% data['id'])
                conexion.close()
                #return {'valid': False, 'tktid': valid[1]}
                return False
            else:
                print("ingresando un nuevo usuario %s"% data['id'])
                sql="insert into telegram(userid, valid, mhash) values (%s, 0, %s)"
                datos=(data['id'], hash)
                cur.execute(sql, datos)
                print("se inserto la fila correctamente hash %s "% hash)
                conexion.commit()
                conexion.close()
                #return {'valid': True, 'tktid': tktid}
                return True
        
        print("ingresando un nuevo usuario final %s"% data['id'])
        sql="insert into telegram(userid, valid, mhash) values (%s, 0, %s)"
        datos=(data['id'], hash)
        cur.execute(sql, datos)
        print("se inserto la fila correctamente final hash %s "% hash)
        conexion.commit()
        conexion.close()
        
        #return {'valid': True, 'tktid': tktid}
        return True
        
    except (Exception) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def config(seccion='MySql', archivo='config.ini'):
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
        params = config('x6nge')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql...storeTwitter')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        # creando la tabla si no existe
        cur.execute("CREATE TABLE IF NOT EXISTS twitter (id bigint(255) not null AUTO_INCREMENT , userid bigint(255) not null, username varchar(255) not null, follow varchar(50) not null, mhash varchar(255) not null, valid int(1) not null, primary key (id))")

        isexist = False
        cur.execute( "SELECT userid, username, follow, mhash, valid FROM twitter where userid=%s and mhash = %s", (id, shash) )
        userlist = cur.fetchall()
        for data in userlist:
            print("____%s____" % data[0])
            if(data[0] == id):
                isexist = True
            
        if(isexist):
            cur.execute( "UPDATE twitter SET username=%s, follow=%s, mhash=%s, valid=%s where userid=%s and mhash = %s", (user, follow, shash, 0, id, shash) )
            conexion.commit()
            print("se actualizo un usuario %s"%user)
            conexion.close()
            return True
        #cur.execute("CREATE INDEX userids ON telegram (userid)")
        sql="insert into twitter(userid, username, follow, mhash, valid) values (%s, %s, %s, %s, 0)"
        datos=(id, user, follow, shash)
        cur.execute(sql, datos)
        conexion.commit()
        print("se inserto un nuevo usuario %s"%user)
        conexion.close()
        return True
        
    except (Exception) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def validateTwitterTelegram(twitter, telegram):
    try:
        conexion = None
        #params = config()
        params = config('x6nge')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql...validateTwitterTelegram')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()

        twitter = twitter.replace('"', '')
        cur.execute( "SELECT valid FROM twitter where mhash=%s LIMIT 0, 1", (twitter, ) )
        vTwitter = cur.fetchone()
        print(vTwitter)
        twittervalid = False
        twitterexist = False
        if(vTwitter and vTwitter is not None):
            twitterexist = True
            if(vTwitter[0] == 0):
                twittervalid = True
            elif(vTwitter[0] == 1):
                twittervalid = False

        if(twittervalid):
            cur.execute( "UPDATE twitter SET valid=1 where mhash=%s", (twitter,) )
            conexion.commit()
            print("______Se seteo ese userr a valid 1 en twitter_______")
        ################################ TELEGRAM #################################
        
        # creación del cursor
        #cur = conexion.cursor()
        
        # creando la tabla si no existe
        telegram = telegram.replace('"', '')
        print("__________%s____________"%telegram)
        cur.execute( "SELECT valid FROM telegram where mhash=%s", (telegram,) )
        vTelegram = cur.fetchone()
        print(vTelegram)
        telegramvalid = False
        telegramexist = False
        if(vTelegram and vTelegram is not None):
            telegramexist = True
            if(vTelegram[0] == 0):
                telegramvalid = True
            elif(vTelegram[0] == 1):
                telegramvalid = False

        if(telegramvalid):
            cur.execute( "UPDATE telegram SET valid=1 where mhash=%s", (telegram,) )
            conexion.commit()
            print("______Se teteo ese userr a valid 1 en telegram_______")

        return {"twitterexist": twitterexist, "twittervalid": twittervalid, "telegramexist": telegramexist, "telegramvalid": telegramvalid}
        
    except (Exception) as error:
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
        params = config('x6nge')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql...validateWallet')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        isexist = False
        cur.execute("CREATE TABLE IF NOT EXISTS metamask (id bigint(255) not null AUTO_INCREMENT, refid varchar(255) not null, wallet varchar(255) not null, tokens bigint(255) not null, referidos bigint(255) not null, refpaid bigint(255) not null, paid int(1) not null, primary key (id))")
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
        
    except (Exception) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def getWallets(basedir):
    try:
        redif = "%s%s"%(uuid.uuid4().hex, uuid.uuid4().hex)
        conexion = None
        #params = config()
        params = config('postgresql')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql...validateWallet')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        isexist = False
        cur.execute("CREATE TABLE IF NOT EXISTS metamask (id bigint(255) not null AUTO_INCREMENT, refid varchar(255) not null, wallet varchar(255) not null, tokens bigint(255) not null, referidos bigint(255) not null, refpaid bigint(255) not null, paid int(1) not null, primary key (id))")
        #cur.execute("CREATE INDEX userids ON telegram (userid)")
        conexion.commit()

        cur.execute( "SELECT wallet, paid, referidos, refpaid FROM metamask")

        # Recorremos los resultados y los mostramos
        returndata = ""
        _token = 0
        _ref_paid = 0
        _ref_token = 0
        _ref_paid_total = 0
        isFile = False

        walletlist = cur.fetchall()
        namefile = "wallets_%s.csv" % getTime()
        filename = os.path.join(basedir, namefile)
        
        with open("wallets.csv","w",encoding='UTF-8') as f:
            writer = csv.writer(f, delimiter=",", lineterminator="\n")
            for wallet, paid, referidos_tot, refpaid in walletlist :
                if(paid == 1):
                    _token = 0
                else:
                    _token = 30
                
                if(referidos_tot > (refpaid + 2)):
                    _ref_to_paid = referidos_tot - refpaid
                    _ref_pend_topaid = _ref_to_paid % 3
                    _ref_paid = _ref_to_paid - _ref_pend_topaid
                    _ref_token = (_ref_paid / 3) * 5
                    _ref_paid_total = _ref_paid + refpaid

                _token = _token + _ref_token

                sql = "UPDATE metamask SET refpaid=%s, paid=1 where wallet=%s"
                data = (_ref_paid_total, wallet)
                cur.execute(sql, data)
                conexion.commit()

                writer.writerow([wallet, _token])
        
            isFile = True
        
        if isFile:
            return namefile
        else:
            return False
        
    except (Exception) as error:
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

def authCode(largo=6):
    numeros = map(lambda x: random.randint(1, 9), range(largo))
    return reduce(lambda x, y: str(x) + str(y), numeros)

def timestamp():
    fecha = "%s" % datetime.now()
    timeret = time.mktime(datetime.strptime(fecha[:19], "%Y-%m-%d %H:%M:%S").timetuple())
    return timeret

def storeCode(id, code, stime, mintime):
    try:
        conexion = None
        #params = config()
        params = config('x6nge')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql... storeCode')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        print("utilizando update time ")
        # creando la tabla si no existe
        cur.execute("CREATE TABLE IF NOT EXISTS telegramcode (id bigint(255) not null AUTO_INCREMENT , userid bigint(255) not null, code bigint(255) not null, fecha int(11) not null, primary key (id))")
        #cur.execute("CREATE INDEX userids ON telegram (userid)")
        
        cur.execute( "SELECT fecha FROM telegramcode where userid=%s", (id, ))
        codes = cur.fetchall()
        
        for cod in codes:
            print("utilizando update time %s "% cod)
            if((stime - cod[0]) > mintime):
                sql="UPDATE telegramcode SET code=%s, fecha=%s WHERE userid=%s;"
                datos=(code, stime, id)
                cur.execute(sql, datos)
                conexion.commit()
                conexion.close()
                return {"response": "store_code_ok"}
            else:
                return {"response": "store_code_timeout"}
                
        print("insertando nueva fila")
        sql="insert into telegramcode (userid, code, fecha) values (%s, %s, %s)"
        datos=(id, code, stime)
        cur.execute(sql, datos)
        conexion.commit()
        conexion.close()
        return {"response": "store_code_ok"}

    except (Exception) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def getStoreCode(id, hash):
    try:
        conexion = None
        #params = config()
        params = config('x6nge')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql...getStoreCode')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        
        #cur.execute( "SELECT userid FROM telegram where mhash=%s", (hash, ) )
        hash = str(hash.replace('"', ""))
        print("__________________%s_________________" % hash)
        cur.execute( "SELECT userid FROM telegram where mhash=%s", (hash, ))
        # Recorremos los resultados y los mostramos
        ids = cur.fetchone()
        print("_____________________%s____________________"%ids)
        
        cur.execute( "SELECT code, fecha FROM telegramcode where userid=%s", (ids[0], ) )
        print("______________________________________-")
        # Recorremos los resultados y los mostramos
        codelist = cur.fetchone()
        code = codelist[0]
        fecha = codelist[1]
        print("los codigos son %s, time %s " % (code, fecha))
        return (code, fecha)

    except (Exception) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def validateTwitter(id, username):
    try:
        conexion = None
        #params = config()
        params = config('x6nge')
        #print(params)
    
        # Conexion al servidor de MySql
        print('Conectando a la base de datos MySql...validateTwitter')
        conexion = mysql.connector.connect(**params)
        print("se conectpo a la base de datos")
        # creación del cursor
        cur = conexion.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS twitter (id bigint(255) not null AUTO_INCREMENT , userid bigint(255) not null, username varchar(255) not null, follow varchar(50) not null, mhash varchar(255) not null, valid int(1) not null, primary key (id))")
        conexion.commit()

        cur.execute( "SELECT valid FROM twitter where userid=%s AND username=%s LIMIT 0, 1", (id, username) )
        vTwitter = cur.fetchone()
        print("la columns es ")
        print(vTwitter)
        twittervalid = False
        twitterexist = False
        if(vTwitter and vTwitter is not None):
            twitterexist = True
            if(vTwitter[0] == 0):
                twittervalid = True
            elif(vTwitter[0] == 1):
                twittervalid = False

        return {"twitterexist": twitterexist, "twittervalid": twittervalid}
        
    except (Exception) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')

def getTime(separador="_"):
    timeA = datetime.now()
    time_D = str(timeA.day)
    if len(time_D) == 1:
        time_D = "0%s" % time_D
    time_M = str(timeA.month)
    if len(time_M) == 1:
        time_M = "0%s" % time_M
    time_Y = str(timeA.year)

    timestamp = "%s_%s_%s" % (time_D, time_M, time_Y)
    return timestamp

#"08122b7065a6e80e465709a380af57c69ecde1fd27f5a05d8c1c1474f1ce27e6"

#"9bbd6b6168abcde2e492529519f91eab59210c423c2d45b3f76e4b2cf62dd0f3"