import pytest

from bot.model import Model


@pytest.mark.async_test
async def test_model():
    class TestModel(Model):
        collection = 'test_model'

    t = TestModel(name='test', value='test', parameter='test',
                  dict_param={'k': 'val'})
    t = await t.save()
    t = await TestModel.get({'_id': t._id})
    assert t.name == 'test'
    assert t.value == 'test'
    assert t.dict_param['k'] == 'val'
