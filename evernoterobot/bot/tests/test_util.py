from bot.util import dict_get, dict_set


def test_dict_get():
    d = {
        'a': {'b': 123},
        'a2': {
            'a3': {
                'a4': 'stop',
                'a5': 2,
            }
        }
    }
    assert isinstance(dict_get(d, ['a']), dict)
    assert dict_get(d, ['a', 'b']) == 123
    assert isinstance(dict_get(d, ['a2', 'a3']), dict)
    assert dict_get(d, ['a2', 'a3', 'a4']) == 'stop'
    assert dict_get(d, ['a2', 'a3', 'a5']) == 2
    assert not dict_get(d, ['a', 'z'])
    assert not dict_get(d, ['a2', 'a3', 'a4', 'a5'])


def test_dict_set():
    d = {}
    dict_set(d, 123, ['x'])
    assert d['x'] == 123
    dict_set(d, {}, ['a'])
    assert isinstance(d['a'], dict)
    dict_set(d, {'x': 'abc'}, ['a', 'b'])
    assert d['a']['b']['x'] == 'abc'
    dict_set(d, 'zzz', ['x'])
    assert d['x'] == 'zzz'
    dict_set(d, 'zzz', ['a', 'b', 'c', 'd', 'e'])
    assert d['a']['b']['c']['d']['e'] == 'zzz'
