import unittest
from bot.data.fields import DateTimeField
from bot.data.models import Model
from datetime import datetime


class TestModel(Model):
    created = DateTimeField(init_current=True)


class TestModels(unittest.TestCase):
    def test_datetime(self):
        now = datetime.now()
        model = TestModel()
        model2 = TestModel()
        assert model.created is not None
        assert model.created.value.year == now.year
        model2.created.value = datetime(1997, 1, 1)
        assert model.created.value.year == 2018
        assert model2.created.value.year == 1997
