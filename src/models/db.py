import os.path
from peewee import MySQLDatabase
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
cur_dir = os.path.abspath(os.path.dirname(__file__))
conf_path = os.path.join(cur_dir, '../conf.ini')
parser.read(conf_path)

DB = MySQLDatabase(parser.get('db', 'DB_NAME'),
                   host=parser.get('db', 'DB_HOST'),
                   user=parser.get('db', 'DB_USER'),
                   password=parser.get('db', 'DB_PASS'),
                   port=parser.getint('db', 'DB_PORT'),
                   use_unicode=True,
                   charset='utf8')

DB_NAME = parser.get('db', 'DB_NAME')
