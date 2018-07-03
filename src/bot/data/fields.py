from datetime import datetime


class Field:
    def __init__(self, **kwargs):
        self._value = None
        self.properties = kwargs

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self.__dict__['_value'] = self.validate(v)

    def validate(self, value):
        return value

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.value)

    def serialize(self):
        return self._value


class DateTimeField(Field):
    def __init__(self, *, init_current=False):
        super().__init__(init_current=init_current)
        self.value = datetime.now() if init_current else None

    def validate(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.strptime(value, '%Y.%m.%d %H:%M:%S')
        if value is None:
            return
        raise Exception('Invalid value \'{}\''.format(value))

    def serialize(self):
        if self.value:
            return self.value.strftime('%Y.%m.%d %H:%M:%S')


class StringField(Field):
    def validate(self, value):
        if isinstance(value, str):
            return value
        return str(value)


class IntegerField(Field):
    def validate(self, value):
        if isinstance(value, int):
            return value
        return int(value)


class StructField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._value = {}
        for field_name, field_value in kwargs.items():
            self._value[field_name] = field_value

    def validate(self, value):
        if not isinstance(value, dict):
            raise Exception('Invalid value \'{}\'. Dict expected.'.format(value))
        if value is None:
            return
        result = {}
        for field_name, field_value in value.items():
            field = self.value.get(field_name)
            if field:
                field.value = field_value
                result[field_name] = field
        return result

    def __setattr__(self, name, value):
        if name in ('_value', 'value', 'properties'):
            return object.__setattr__(self, name, value)
        field = self.value.get(name)
        if field and isinstance(field, Field):
            field.value = value

    def __getattr__(self, name):
        field = self.__dict__.get(name)
        if field and isinstance(field, Field):
            return field.value
        return field

    def serialize(self):
        data = {}
        for attr_name, field in self._value.items():
            value = field.serialize()
            if value is not None:
                data[attr_name] = value
        return data


class BooleanField(Field):
    def validate(self, value):
        if isinstance(value, bool):
            return value
        return bool(value)


class EnumField(Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        values = kwargs.get('values')
        if not isinstance(values, list):
            raise Exception('Invalid type. "list" expected.')
        self.possible_values = values

    def validate(self, value):
        if value not in self.possible_values:
            raise Exception('Invalid value "{0}"'.format(value))
        return value
