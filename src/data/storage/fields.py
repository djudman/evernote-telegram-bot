from datetime import datetime


class Field:
    def validate(self, value):
        return value

    def get_initial_value(self):
        return


class DateTimeField(Field):
    def __init__(self, init_current=False):
        self.init_current = init_current

    def validate(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.strptime(value, '%Y.%m.%d %H:%M:%S')
        if value is None:
            return
        raise Exception('Invalid value \'{}\''.format(value))

    def get_initial_value(self):
        if not self.init_current:
            return
        return datetime.now()


class StringField(Field):
    def validate(self, value):
        if value is None:
            return
        if isinstance(value, str):
            return value
        return str(value)


class IntegerField(Field):
    def validate(self, value):
        if value is None:
            return
        if isinstance(value, int):
            return value
        return int(value)


class FloatField(Field):
    def validate(self, value):
        if value is None:
            return
        if isinstance(value, float):
            return value
        return float(value)


class StructField(Field):
    def __init__(self, **kwargs):
        self._fields = kwargs

    def get_fields(self):
        return self._fields

    # def validate(self, value):
    #     if not isinstance(value, dict):
    #         return value
    #     validated_value = StructField(**self._attrs)
    #     for field_name, field_value in value.items():
    #         setattr(validated_value, field_name, field_value)
    #     return validated_value


class BooleanField(Field):
    def validate(self, value):
        if isinstance(value, bool):
            return value
        return bool(value)


class EnumField(Field):
    def __init__(self, values):
        self._possible_values = values

    def validate(self, value):
        if value is None:
            value = self._possible_values[0]
        if value not in self._possible_values:
            raise Exception('Invalid value "{0}"'.format(value))
        return value
