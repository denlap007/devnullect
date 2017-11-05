from peewee import Model
from db import DB


class MyBaseModel(Model):
    class Meta:
        database = DB
