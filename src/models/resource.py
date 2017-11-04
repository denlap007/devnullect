from peewee import PrimaryKeyField, CharField, DateTimeField
from theBaseModel import MyBaseModel


class Resource(MyBaseModel):
    id = PrimaryKeyField(db_column="id")
    rs_content = CharField(2000)
    rs_date = DateTimeField()

    class Meta:
        order_by = ('id',)
        db_table = 'resource'
