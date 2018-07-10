import unittest
from bot.core.fields import BooleanField
from bot.core.fields import DateTimeField
from bot.core.fields import EnumField
from bot.core.fields import IntegerField
from bot.core.fields import StringField
from bot.core.fields import StructField
from bot.core.models import Model
from datetime import datetime


class TestModel(Model):
    created = DateTimeField(init_current=True)
    name = StringField()
    data = StructField(
        info=StructField(
            count=IntegerField()
        ),
        name=StringField()
    )
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
        # save_data = model.save_data()
        # assert save_data['mode'] == 'one'

    def test_struct(self):
        model = TestModel({'data': {'info': {'count': 123}}})
        self.assertEqual(model.data.info.count, 123)
        model.data.info.count = 5
        self.assertEqual(model.data.info.count, 5)
        model.data.from_dict({ 'info': { 'count': 10 } })
        self.assertEqual(model.data.info.count, 10)
        self.assertIsNone(model.name)
