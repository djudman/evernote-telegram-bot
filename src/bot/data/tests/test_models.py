import unittest
from bot.data.fields import BooleanField
from bot.data.fields import DateTimeField
from bot.data.fields import EnumField
from bot.data.fields import IntegerField
from bot.data.fields import StringField
from bot.data.fields import StructField
from bot.data.models import Model
from datetime import datetime


class TestModel(Model):
    created = DateTimeField(init_current=True)
    name = StringField()
    data = StructField()
    mode = EnumField(values=['one', 'two'])
    enabled = BooleanField()
    amount = IntegerField()


class TestModels(unittest.TestCase):
    def test_datetime(self):
        now = datetime.now()
        model = TestModel()
        model2 = TestModel()
        assert model.created is not None
        assert model.created.year == now.year
        model2.created = datetime(1997, 1, 1)
        assert model.created.year == 2018
        assert model2.created.year == 1997

    def test_string(self):
        model = TestModel()
        model2 = TestModel()
        assert model.name is None
        model.name = 'Test'
        assert model.name == 'Test'
        assert model2.name is None

    @unittest.expectedFailure
    def test_enum_invalid_value(self):
        model = TestModel()
        model.mode = 'three'

    def test_enum(self):
        model = TestModel()
        model.mode = 'one'
        assert model.mode == 'one'
        save_data = model.save_data()
        assert save_data['mode'] == 'one'
