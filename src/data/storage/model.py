import re
from datetime import datetime
from .fields import Field
from .fields import StructField


def storage(provider=None, db=None, collection=None):
    def wrapper(model_class):
        config = {}
        if provider:
            config['provider'] = provider
        if db:
            config['db'] = db
        if collection:
            config['collection'] = collection
        setattr(model_class, 'config', config)
        return model_class
    return wrapper


class Model:
    def __init__(self, data: dict, *, fields=None, storage=None):
        self.id = data.get('id')
        self.config = {
            'fields': fields or {},
            'storage': storage,
        }
        for name, field in self.get_fields().items():
            if isinstance(field, StructField):
                self._init_struct_field(name, field)
            else:
                setattr(self, name, field.get_initial_value())
        self.from_dict(data)
        self._created = datetime.now()

    def __repr__(self):
        attrs = {'id': self.id}
        for name in self.get_fields().keys():
            value = getattr(self, name)
            attrs[name] = value
        address = hex(id(self))
        classname = self.__class__.__name__
        return '<{0} {1}>({2})'.format(classname, address, attrs)

    def __setattr__(self, name, value):
        if hasattr(self, '_created'):
            fields = self.get_fields()
            field = fields.get(name)
            if field:
                value = field.validate(value)
        return object.__setattr__(self, name, value)


    # def _camelcase_to_underscore(self, string):
    #     s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    #     return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def get_fields(self):
        if not self.config['fields']:
            class_attrs = vars(self.__class__)
            for name, field in class_attrs.items():
                if isinstance(field, Field):
                    self.config['fields'][name] = field
        return self.config['fields']

    def _init_struct_field(self, struct_field_name, struct_field):
        nested_fields = struct_field.get_fields()
        model = Model({}, fields=nested_fields)
        for name, field in nested_fields.items():
            if isinstance(field, StructField):
                model._init_struct_field(name, field)
                continue
            setattr(model, name, field.get_initial_value())
        setattr(self, struct_field_name, model)

    def from_dict(self, data: dict):
        if not isinstance(data, dict):
            raise Exception('Invalid data type. Dict expected.')
        fields = self.get_fields()
        for name, field in fields.items():
            value = data.get(name)
            if value is None:
                continue
            if isinstance(value, dict):
                if not isinstance(field, StructField):
                    raise Exception('Invalid value for field "{}"'.format(name))
                model = Model({}, fields=field.get_fields())
                model.from_dict(value)
                value = model
            setattr(self, name, value)

    def to_dict(self):
        data = {'id': self.id} if self.id else {}
        for name, field in self.get_fields().items():
            value = getattr(self, name)
            if isinstance(field, StructField):
                value = value.to_dict()
            data[name] = value
        return data

    def save(self):
        storage = self.config['storage']
        if not storage:
            raise Exception('Storage not configured')
        save_data = self.to_dict()
        if not self.id:
            self.id = storage.provider.insert(save_data)
        else:
            result = storage.provider.update({'id': self.id}, save_data)
            if result['matched'] == 0:
                self.id = storage.provider.insert(save_data)

    def delete(self):
        storage = self.config.get('storage')
        if not storage:
            raise Exception('Storage not configured')
        storage.provider.delete({'id': self.id})
