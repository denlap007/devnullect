from peewee import BigIntegerField, CharField
from theBaseModel import MyBaseModel


class Group(MyBaseModel):
    id = BigIntegerField(primary_key=True, db_column="id")
    g_name = CharField(50)

    class Meta:
        order_by = ('id',)
        db_table = 'group'
