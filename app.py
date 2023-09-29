from flask import Flask, request, redirect, session, url_for, render_template
from flask_cors import CORS
from telethon.errors.rpcerrorlist import PeerFloodError
import os
import asyncio
import psycopg2
import time

from config.config import startConnection, validateUsername, validUserFromDb, config, calculate_sha256, storeTwitter, validateTwitterTelegram, validateWallet, authCode, timestamp, storeCode

######################## TWITTER OAUTH ######################
from requests_oauthlib import OAuth1Session
import json
import requests
#############################################################

_TOKEN_ = 'tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s'
_TIMEMAX_ = 600
######################## TWITTER OAUTH ######################
consumer_key='Gi22eaK49RxNH9uYhJquV0v4u'
consumer_secret= 'rQJKpa4p8j8Pc1Ju9llERSDyCcj6NuKwyXrGJy4wHFYcDIU923'

web_url = "http://localhost:8080"
request_token_url = "https://api.twitter.com/oauth/request_token"
access_token_url = "https://api.twitter.com/oauth/access_token"

fields = "created_at,description"
params = {"user.fields": fields}

#############################################################

# http://127.0.0.1:5000/api/telegram?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s&user=kalguanchez&group=thekeyoftrueTKT&type=broadcast
# http://127.0.0.1:5000/api/telegram?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s&user=Davier&group=thekeyoftrueTKT&type=broadcast
# http://127.0.0.1:5000/api/cleandb?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s
# http://127.0.0.1:5000/api/updatebd?token=tktk9wv7I8UU26FGGhtsSyMgZv8caqygNgPVMrdDw02IZlnRhbK3s&user=5900098531
# postgres://telegrambot_tkt_user:7p2uqGFWiPARqzIyEsOcsqRv00C0g50e@dpg-ck68gl5drqvc73bj9kpg-a.oregon-postgres.render.com/telegrambot_tkt
# gunicorn --bind 0.0.0.0:8000 app:app


"""
task = asyncio.create_task(startConnection())
res = await asyncio.shield(task)
while True:
   
    if task.done():
        client = task.result()
        break
"""

app = Flask(__name__, instance_relative_config=False)
app.secret_key = os.urandom(50)
#CORS(app, supports_credentials=True)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

######################## TWITTER OAUTH ######################
@app.route("/", methods=["GET"])
def index():
    
    ip = '%s' % request.remote_addr
    ip = ip.replace('.', '')
    
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print(
            "There may have been an issue with the consumer_key or consumer_secret you entered."
        )

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    
    #session['ip'] = {'resource_owner_key': resource_owner_key, "resource_owner_secret": resource_owner_secret}
    session["%s1"%ip] = resource_owner_key
    session["%s2"%ip]  = resource_owner_secret

    # # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    
    return redirect(authorization_url)

@app.route("/oauth/callback", methods=["GET"])
def callback():
    ip = '%s' % request.remote_addr
    ip = ip.replace('.', '')
    
    resource_owner_key = session["%s1"%ip]
    resource_owner_secret = session["%s2"%ip]

    print("Got OAuth token: %s" % resource_owner_key)

    verifier = request.args.get("oauth_verifier")
    print("el toen de verificacion %s"%verifier)
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]

    # Make the request
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    response = oauth.get("https://api.twitter.com/2/users/me", params=params)

    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(response.status_code, response.text)
        )

    print("Response code: {}".format(response.status_code))

    json_response = response.json()
    print(json_response)

    #http://localhost:5001/auth?token=tktk9wv7I8UU26FGGhtsSyMgZvmco8caqygNgPVMrdDw02IZlnRhbK3s&username=lii_mmminseon5
    resp = requests.get('http://localhost:5001/auth?token=tktk9wv7I8UU26FGGhtsSyMgZvmco8caqygNgPVMrdDw02IZlnRhbK3s&username={}'.format(json_response['data']['username']))
    if resp.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                resp.status_code, resp.text
            )
        )
    jresponse = resp.json()
    isfollow = jresponse['response']
    print(jresponse)

    mId = json_response['data']['id']
    mUsername = json_response['data']['id']

    if(isfollow == 'username_follows'):
        mFollow = 'valid'
    elif(isfollow == 'username_not_follow'):
        mFollow = 'invalid'
    elif(isfollow == 'username_not_exist'):
        mFollow = 'notexist'

    hash_value = calculate_sha256('%s %s %s'%(mId, mUsername, mFollow))

    storeTwitter(mId, mUsername, mFollow, hash_value)

    #print(json.dumps(json_response, indent=4, sort_keys=True))
    return redirect('%s/api/twitter?token=%s&username=%s&twitter=%s&hash=%s'%(web_url, _TOKEN_, mUsername, mFollow, hash_value))

#############################################################

@app.route('/api/telegram', methods=["GET"])
async def telegramget():
    token = request.args.get('token')
    user = request.args.get('user')
    group = request.args.get('group')
    type = request.args.get('type')
    print(token+" "+user+" "+group+" "+type)

    if(_TOKEN_ != token):
        return app.response_class(
            response=json.dumps({'response': 'invalid Token'}),
            status=200,
            mimetype='application/json'
        )
    
    client = await startConnection()
    userdata = await validateUsername(client, group, type, user)
    await client.disconnect()

    returndata = ""

    if(userdata):
        valid = validUserFromDb(userdata)
        hash_value = calculate_sha256("%s %s %s" % (userdata['id'], userdata['name'], userdata['username']))
        print("validando desde bd %s"%valid)
        if(valid):
            returndata = {'response': 'user_ok', 'hash': hash_value}
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

@app.route('/api/telegram', methods=["POST"])
async def telegram():
    data = request.get_json()
    user = data["username"]
    token = data["token"]
    group = data["group"]
    type = data["type"]
    print(token+" "+user+" "+group+" "+type)
    #time.sleep(4)
    #return {'response': 'user_ok', 'data': "okok"}
    if(_TOKEN_ != token):
        return app.response_class(
            response=json.dumps({'response': 'invalid Token'}),
            status=200,
            mimetype='application/json'
        )
    
    client = await startConnection()
    userdata = await validateUsername(client, group, type, user)
    
    returndata = ""
    

    if(userdata):
        hash_value = calculate_sha256("%s %s %s" % (userdata['id'], userdata['name'], userdata['username']))
        valid = validUserFromDb(userdata, hash_value)
        
        print("validando desde bd %s"%valid)
        if(valid):
            receiver = await client.get_input_entity(user)
            storeCode()
            message = authCode()
            session["%s_message" % user] = message
            session["%s_time" % user] = timestamp()
            try:
                await client.send_message(receiver, message.format(user))
            except PeerFloodError:
                print("[!] Getting Flood Error from telegram. \n[!] Script is stopping now. \n[!] Please try again after some time.")
            except Exception as e:
                print("[!] Error:", e)
                print("[!] Trying to continue...")

            returndata = {'response': 'user_ok', "hash": hash_value}
        else:
            returndata = {'response': 'user_exist'}
    else:
        receiver = await client.get_input_entity(user)
        message = authCode()
        session['message'] = message
        session["message_%s" % user] = "%s" % message
        session["time_%s" % user] = "%s" % timestamp()
        try:
            await client.send_message(receiver, message.format(user))
            print("se envio el message codde sin registrarse %s" % message)
        except PeerFloodError:
            print("[!] Getting Flood Error from telegram. \n[!] Script is stopping now. \n[!] Please try again after some time.")
        except Exception as e:
            print("[!] Error:", e)
            print("[!] Trying to continue...")
        returndata = {'response': "user_not_registry"}

    await client.disconnect()

    response = app.response_class(
        response=json.dumps(returndata),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/api/telegram/code', methods=["POST"])
async def telegramCode():
    data = request.get_json()
    token = data["token"]
    user = data["username"]
    code = data["code"]
    
    #time.sleep(4)
    #return {'response': 'user_ok', 'data': "okok"}
    if(_TOKEN_ != token):
        return app.response_class(
            response=json.dumps({'response': 'invalid Token'}),
            status=200,
            mimetype='application/json'
        )
    print("el sms guardao es %s" % session['message'])
    timeactual = timestamp()
    msg = "message_%s" % user
    tim = "time_%s" % user
    message = session[msg]
    timeant = session[tim]

    session[msg] = ''
    session[tim] = ''

    returndata = ""

    timedif = timeant - timeactual
    print("print el timedef es %s el msg %s el tim %s " % (timedif, message, timeant))
    if(timedif <= _TIMEMAX_):
        if(code == message):
            returndata = {'response': 'code_ok'}
        else:
            returndata = {'response': 'user_error'}
    else:
        returndata = {'response': 'user_error_time'}
    

    response = app.response_class(
        response=json.dumps(returndata),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/api/cleandb', methods=["GET"])
def cleandb():
    token = request.args.get('token')

    if(_TOKEN_ != token):
        return app.response_class(
            response=json.dumps({'response': 'invalid Token'}),
            status=200,
            mimetype='application/json'
        )
    
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

@app.route('/api/updatebd', methods=["GET"])
def updatebd():
    token = request.args.get('token')
    user = request.args.get('user')
    value = request.args.get('value')
    if(_TOKEN_ != token):
        return app.response_class(
            response=json.dumps({'response': 'invalid Token'}),
            status=200,
            mimetype='application/json'
        )
    if(user == None or user == ""):
        return app.response_class(
            response=json.dumps({'response': 'invalid User'}),
            status=200,
            mimetype='application/json'
        )
    
    if(value == None):
        value = 1

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
        sql = "UPDATE telegram SET valid=%s WHERE userid=%s;"
        cur.execute(sql, (value, user))
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

@app.route('/api/getusers', methods=["GET"])
def getusers():
    token = request.args.get('token')
    user = request.args.get('user')
    if(_TOKEN_ != token):
        return app.response_class(
            response=json.dumps({'response': 'invalid Token'}),
            status=200,
            mimetype='application/json'
        )
    if(user == None or user == ""):
        return app.response_class(
            response=json.dumps({'response': 'invalid User'}),
            status=200,
            mimetype='application/json'
        )
    
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

####################AUTENTICATE WALLET##################
@app.route('/api/wallet', methods=["POST"])
async def wallet():
    data = request.get_json()
    token = data["token"]
    wallet = data["wallet"]
    twitter = data["twitter"]
    telegram = data["telegram"]
    referido = data["referido"]

    #return {'response': 'user_ok', 'data': "okok"}
    if(_TOKEN_ != token):
        return app.response_class(
            response=json.dumps({'response': 'invalid Token'}),
            status=200,
            mimetype='application/json'
        )
    returndata = ""

    val = validateTwitterTelegram(twitter, telegram)

    isok =False
    if(val['twitterexist'] and val['telegramexist']):
        if(not val['twittervalid']):
            returndata = {'response': 'user_twitter_exist'}
        else:
            if(not val['telegramvalid'] ):
                returndata = {'response': 'user_telegram_exist'}
            else:
                isok = True
        
    elif(not val['twitterexist']):
        returndata = {'response': 'user_twitter_notexist'}

    elif(not val['telegramexist']):
        returndata = {'response': 'user_telegram_notexist'}

    if(isok):
        vWallet = validateWallet(wallet, referido)
        if(vWallet[0] == 'notpaid'):
            returndata = {'response': 'user_wallet_notpaid', "data": vWallet[1]}
        elif vWallet[0] == 'paid':
            returndata = {'response': 'user_wallet_paid', "data": vWallet[1]}
        elif vWallet[0] == 'ok':
            returndata = {'response': 'user_wallet_ok', "data": vWallet[1], "reflink": vWallet[2]}

    response = app.response_class(
        response=json.dumps(returndata),
        status=200,
        mimetype='application/json'
    )
    return response
########################################################
@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*" # <- You can change "*" for a domain for example "http://localhost"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization"
    return response


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5000, debug=True)
