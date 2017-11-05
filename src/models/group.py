from peewee import BigIntegerField
from theBaseModel import MyBaseModel


class Group(MyBaseModel):
    id = BigIntegerField(primary_key=True, db_column="id")

    class Meta:
        order_by = ('id',)
        db_table = 'group'