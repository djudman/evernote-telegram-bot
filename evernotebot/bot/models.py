from evernotebot.data.storage.fields import DateTimeField
from evernotebot.data.storage.fields import EnumField
from evernotebot.data.storage.fields import FloatField
from evernotebot.data.storage.fields import IntegerField
from evernotebot.data.storage.fields import StringField
from evernotebot.data.storage.fields import StructField
from evernotebot.data.storage.model import Model
from evernotebot.data.storage.model import storage


@storage(collection='users')
class User(Model):
    created = DateTimeField(init_current=True)
    last_request_time = DateTimeField()
    bot_mode = EnumField(values=['one_note', 'multiple_notes'])
    state = StringField()
    telegram = StructField(
        first_name=StringField(),
        last_name=StringField(),
        username=StringField(),
        chat_id=IntegerField(),
    )
    evernote = StructField(
        access=StructField(
            token=StringField(),
            permission=EnumField(values=['basic', 'full'])
        ),
        notebook=StructField(
            name=StringField(),
            guid=StringField()
        ),
        shared_note_id=StringField(),  # NOTE: uses in 'one_note' mode
        oauth=StructField(
            token=StringField(),
            secret=StringField(),
            callback_key=StringField(),
            app_key=StringField()  # TODO: it seems this field is unused
        )
    )
