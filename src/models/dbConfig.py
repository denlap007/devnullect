from peewee import MySQLDatabase, OperationalError
import logging
import time
from user import User
from theList import List
from resourceList import ResourceList
from resource import Resource
from db import DB

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    num_of_retries = 30
    time_interval__in_secs = 1
    # connect to db explicitely, will reveal errors
    for _ in range(num_of_retries):
        try:
            DB.connect()
            # perform db -vendor dependant operations if necessary
            prepareTables()
            # create db tables if they do not exist
            DB.create_tables([User, List, ResourceList, Resource], safe=True)
            break
        except OperationalError:
            time.sleep(time_interval__in_secs)
        except Exception as e:
            logger.error(str(e))
            raise
    else:
        raise


def prepareTables():
    # MySQL specific preparation
    if isinstance(DB, MySQLDatabase):
        prepareMySQLTables()


def prepareMySQLTables():
    # set default tables charset and collation
    DB.execute_sql("SET NAMES utf8 COLLATE utf8_general_ci;")
