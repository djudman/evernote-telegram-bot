# import unittest
# from data.storage.fields import BooleanField
# from data.storage.fields import DateTimeField
# from data.storage.fields import EnumField
# from data.storage.fields import IntegerField
# from data.storage.fields import StringField
# from data.storage.fields import StructField
# from data.storage.model import Model
# from datetime import datetime


# class TestModel(Model):
#     created = DateTimeField(init_current=True)
#     name = StringField()
#     data = StructField(
#         info=StructField(
#             count=IntegerField()
#         ),
#         name=StringField()
#     )
#     mode = EnumField(values=['one', 'two'])
#     enabled = BooleanField()
#     amount = IntegerField()


# class TestModels(unittest.TestCase):
#     def test_datetime(self):
#         now = datetime.now()
#         model = TestModel(None, {})
#         model2 = TestModel(None, {})
#         assert model.created is not None
#         assert model.created.year == now.year
#         model2.created = datetime(1997, 1, 1)
#         assert model.created.year == 2018
#         assert model2.created.year == 1997

#     def test_string(self):
#         model = TestModel(None, {})
#         model2 = TestModel(None, {})
#         assert model.name is None
#         model.name = 'Test'
#         assert model.name == 'Test'
#         assert model2.name is None

#     @unittest.expectedFailure
#     def test_enum_invalid_value(self):
#         model = TestModel(None, {})
#         model.mode = 'three'

#     def test_enum(self):
#         model = TestModel(None, {})
#         model.mode = 'one'
#         assert model.mode == 'one'
#         save_data = model.to_dict()
#         assert save_data['mode'] == 'one'

#     def test_struct(self):
#         model = TestModel(storage=None, data={'data': {'info': {'count': 123}}})
#         self.assertEqual(model.data.info.count, 123)
#         model.data.info.count = 5
#         self.assertEqual(model.data.info.count, 5)
#         model.data.from_dict({ 'info': { 'count': 10 } })
#         self.assertEqual(model.data.info.count, 10)
#         self.assertIsNone(model.name)
