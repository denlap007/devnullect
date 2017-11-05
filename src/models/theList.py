from peewee import CharField, PrimaryKeyField, BooleanField, ForeignKeyField
from user import User
from theBaseModel import MyBaseModel


class List(MyBaseModel):
    id = PrimaryKeyField(db_column="id")
    title = CharField(50)
    active = BooleanField(default=False)
    user_id = ForeignKeyField(
        User, db_column='user_id', related_name='users', to_field='id')

    class Meta:
        order_by = ('title',)
        db_table = 'list'
        indexes = (
            # create a unique constraint
            (('title', 'user_id'), True),
        )
