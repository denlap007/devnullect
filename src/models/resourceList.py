from peewee import CharField, PrimaryKeyField, BooleanField, ForeignKeyField
from theList import List
from resource import Resource
from theBaseModel import MyBaseModel


class ResourceList(MyBaseModel):
    id = PrimaryKeyField(db_column="id")
    resource_id = ForeignKeyField(Resource, db_column='resource_id', related_name='resources', to_field='id')
    list_id = ForeignKeyField(List, db_column='list_id', related_name='lists', to_field='id')

    class Meta:
        order_by = ('id',)
        db_table = 'resource_list'
