from peewee import MySQLDatabase
from ConfigParser import SafeConfigParser

conf = SafeConfigParser()
conf.read('../conf.ini')

DB = MySQLDatabase(conf.get('db', 'DB_NAME'),
                   host=conf.get('db', 'DB_HOST'),
                   user=conf.get('db', 'DB_USER'),
                   password=conf.get('db', 'DB_PASS'),
                   port=conf.getint('db', 'DB_PORT'),
                   use_unicode=True,
                   charset='utf8')
