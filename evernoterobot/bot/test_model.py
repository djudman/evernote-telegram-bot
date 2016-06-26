import pytest

from bot.model import Model


@pytest.mark.async_test
async def test_model():
    class TestModel(Model):
        collection = 'test_model'

    t1 = TestModel(name='test', value='test', parameter='test',
                   dict_param={'k': 'val'})
    t = await t1.save()

    t = await TestModel.get({'_id': t1._id})
    assert t._id
    assert t.name == 'test'
    assert t.value == 'test'
    assert t.dict_param['k'] == 'val'
    t.name = 'wooo'
    await t.save()

    t2 = await TestModel.get({'_id': t1._id})
    assert t2.name == 'wooo'
