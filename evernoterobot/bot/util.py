from typing import List


def dict_get(dict_obj: dict, path: List[str]):
    pointer = dict_obj
    for step in path:
        if isinstance(pointer, dict) and pointer.get(step) is not None:
            pointer = pointer[step]
        else:
            return
    return pointer


def dict_set(dict_obj: dict, value, path: List[str]):
    n = len(path)
    pointer = dict_obj
    for i, step in enumerate(path):
        if i < (n - 1):
            if not pointer.get(step):
                pointer[step] = {}
            if not isinstance(pointer[step], dict):
                raise Exception('Invalid path')
            pointer = pointer[step]
        else:
            pointer[step] = value
    return dict_obj

