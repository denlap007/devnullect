from peewee import CharField, PrimaryKeyField, BooleanField, ForeignKeyField
from user import User
from theBaseModel import MyBaseModel


class GroupUser(MyBaseModel):
    id = PrimaryKeyField(db_column="id")
    user_id = ForeignKeyField(
        User, db_column='user_id', related_name='users', to_field='id')
    group_id = ForeignKeyField(
        User, db_column='group_id', related_name='group', to_field='id')

    class Meta:
        order_by = ('id',)
        db_table = 'group_user'
