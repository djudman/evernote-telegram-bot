from bot.model import Model


def test_model():
    class TestModel(Model):
        save_fields = ['name', 'value', 'parameter', 'dict_param']

    t1 = TestModel(name='test', value='test', parameter='test', dict_param={'k': 'val'})
    t1.save()

    t = TestModel.get({'id': t1.id})
    assert t.id
    assert t.name == 'test'
    assert t.value == 'test'
    assert t.dict_param['k'] == 'val'
    t.name = 'wooo'
    t.save()

    t2 = TestModel.get({'id': t1.id})
    assert t2.name == 'wooo'

    new_t = TestModel.create(name='new', value='val')
    assert new_t.name == 'new'
    assert new_t.value == 'val'

    t = TestModel.get({ 'name': 'new' })
    assert t.value == 'val'
