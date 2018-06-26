from datetime import datetime

from bot.data.fields import DateTimeField
from bot.data.fields import EnumField
from bot.data.fields import Field
from bot.data.fields import IntegerField
from bot.data.fields import StringField
from bot.data.fields import StructField


class Model:
    def __init__(self, data=None):
        self.storage = None
        for name, value in vars(self.__class__).items():
            if isinstance(value, Field):
                self.__dict__[name] = value.__class__(**value.properties)
        if data is None:
            data = {}
        for name, value in data.items():
            field = self.__dict__.get(name)
            if field:
                field.value = value

    def save_data(self):
        data = {}
        for field_name, field_value in self.__dict__.items():
            if not isinstance(field_value, Field):
                continue
            value = field_value.serialize()
            if value is not None:
                data[field_name] = value
        return data

    def save(self):
        save_data = self.save_data()
        if not self.storage:
            raise Exception('No storage')
        if hasattr(self, 'id'):
            obj = self.storage.get(self.id)
            self.storage.save(obj)
        else:
            self.storage.insert(save_data)

    def __setattr__(self, name, value):
        field = self.__dict__.get(name)
        if field and isinstance(field, Field):
            field.value = value
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        field = self.__dict__.get(name)
        if field and isinstance(field, Field):
            return field.value
        return field


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
