import configparser
import csv
import time
import psycopg2
from configparser import ConfigParser

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

def validUserFromDb(data):
    conexion = None
    params = config()
    #print(params)
 
    # Conexion al servidor de PostgreSQL
    print('Conectando a la base de datos PostgreSQL...')
    conexion = psycopg2.connect(**params)
    
    # creación del cursor
    cur = conexion.cursor()
    
    # creando la tabla si no existe
    print('La version de PostgreSQL es la:')
    cur.execute("CREATE TABLE IF NOT EXISTS telegram (id serial not null, userid bigint not null, primary key (id))")
    #cur.execute("CREATE INDEX userids ON telegram (userid)")

    cur.execute( "SELECT userid FROM telegram" )

    # Recorremos los resultados y los mostramos
    isexist = False
    userlist = cur.fetchall()
    print("userlist %s" % userlist)
    for userid in userlist :
        print("obteniendo datos de bd %s - %s" % (userid, data['id']))
        if(userid[0] == data['id']):
            print("el usuario ya existe en la bd")
            isexist = True
            break
    if(isexist):
        return False

    sql="insert into telegram(userid) values (%s)"
    datos=(data['id'],)
    print("se esta agregando el usuario con id %s" % data['id'])
    cur.execute(sql, datos)
    conexion.commit()
    print("se agrego el usuario con id %s" % data['id'])

    cur.execute("DELETE * FROM telegram")
    conexion.commit()
    # Cierre de la comunicación con PostgreSQL
    cur.close()
    """
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
        cur.execute('CREATE TABLE telegrambot_tkt.telegram (id BIGINT(255) NOT NULL AUTO_INCREMENT , userid BIGINT(255) NOT NULL, PRIMARY KEY (id), INDEX (id, userid)) ENGINE = InnoDB;')
 
        cur.execute( "SELECT userid FROM telegram" )

        # Recorremos los resultados y los mostramos
        for userid in cur.fetchall() :
            if(userid == data['id']):
                return False

        sql="insert into telegram(userid) values (%s)"
        datos=(data['id'])
        cur.execute(sql, datos)
       
        # Cierre de la comunicación con PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conexion is not None:
            conexion.close()
            print('Conexión finalizada.')
    """

data = {"id": 97082802522}
validUserFromDb(data)