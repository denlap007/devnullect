from peewee import CharField, PrimaryKeyField, BooleanField, ForeignKeyField
from user import User
from group import Group
from theBaseModel import MyBaseModel


class GroupUser(MyBaseModel):
    id = PrimaryKeyField(db_column="id")
    user_id = ForeignKeyField(
        User, db_column='user_id', related_name='the-users', to_field='id')
    group_id = ForeignKeyField(
        Group, db_column='group_id', related_name='groups', to_field='id')

    class Meta:
        order_by = ('id',)
        db_table = 'group_user'
