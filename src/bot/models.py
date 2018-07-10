from bot.core.fields import DateTimeField
from bot.core.fields import EnumField
from bot.core.fields import IntegerField
from bot.core.fields import StringField
from bot.core.fields import StructField


class User(Model):
    collection = 'users'

    created = DateTimeField(init_current=True)
    last_request_time = DateTimeField()
    bot_mode = EnumField(values=['one_note', 'multiple_notes'])
    telegram = StructField(
        first_name=StringField(),
        last_name=StringField(),
        username=StringField(),
        chat_id=IntegerField()
    )
    evernote = StructField(
        access_token=StringField(),
        notebook=StructField(
            name=StringField(),
            guid=StringField()
        ),
        oauth=StructField(
            token=StringField(),
            secret=StringField(),
            url=StringField(),
            callback_key=StringField(),
            app_key=StringField()
        )
    )
