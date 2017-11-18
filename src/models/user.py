from peewee import BigIntegerField, CharField
from theBaseModel import MyBaseModel


class User(MyBaseModel):
    id = BigIntegerField(primary_key=True, db_column="id")
    f_name = CharField(50)
    l_name = CharField(50)

    class Meta:
        order_by = ('id',)
        db_table = 'user'
