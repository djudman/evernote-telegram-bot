from data.storage.fields import DateTimeField
from data.storage.fields import EnumField
from data.storage.fields import FloatField
from data.storage.fields import IntegerField
from data.storage.fields import StringField
from data.storage.fields import StructField
from data.storage.model import Model
from data.storage.model import storage


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


@storage(collection='message_logs')
class MessageLogEntry(Model):
    created = DateTimeField(init_current=True)
    user_id = IntegerField()
    message_type = EnumField(values=['text', 'voice', 'audio', 'photo', 'video', 'document', 'location'])
    request_duration = FloatField()
