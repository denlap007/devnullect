from peewee import MySQLDatabase

DB_NAME = '${DB_NAME}'
DB_HOST = '${DB_HOST}'
DB_USER = '${DB_USER}'
DB_PASS = '${DB_PASS}'
DB_PORT = ${DB_PORT}

DB = MySQLDatabase(DB_NAME, host=DB_HOST, user=DB_USER, password=DB_PASS, port=DB_PORT)
