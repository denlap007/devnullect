from peewee import MySQLDatabase, OperationalError
from functools import wraps
import logging
import time
from user import User
from theList import List
from resourceList import ResourceList
from resource import Resource
from group import Group
from groupUser import GroupUser
from db import DB, DB_NAME

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
            DB.create_tables([User, List, ResourceList, Resource, Group, GroupUser], safe=True)
            # close connection
            DB.close()
            break
        except OperationalError:
            time.sleep(time_interval__in_secs)
        except Exception as e:
            logger.error(str(e))
            raise
    else:
        raise


def handle_db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        num_of_retries = 60
        time_interval__in_secs = 0.5
        for _ in range(num_of_retries):
            try:
                DB.connect()
                func(*args, **kwargs)
                if not DB.is_closed():
                    DB.close()
                break
            except OperationalError:
                time.sleep(time_interval__in_secs)
            except Exception as e:
                logger.error(str(e))
                raise
        else:
            raise
    return wrapper


def prepareTables():
    # MySQL specific preparation
    if isinstance(DB, MySQLDatabase):
        prepareMySQLTables()


def prepareMySQLTables():
    # set default tables charset and collation
    DB.execute_sql('ALTER DATABASE {} DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci'.format(DB_NAME))
