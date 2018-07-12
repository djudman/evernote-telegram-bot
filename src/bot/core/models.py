from datetime import datetime
from bot.core.fields import Field
from bot.core.fields import StructField


class Model:
    def __init__(self, data=None):
        self.storage = None
        self.__fields = {}
        for name, field in self.fields.items():
            if isinstance(field, StructField):
                self.__init_struct_field(name, field)
            else:
                setattr(self, name, field.get_initial_value())
        if data:
            self.from_dict(data)

    @property
    def fields(self):
        if not self.__fields:
            for name, value in vars(self.__class__).items():
                if isinstance(value, Field):
                    self.__fields[name] = value
        return self.__fields

    def __init_struct_field(self, name, field):
        model = Model()
        for inner_name, inner_field in field.fields.items():
            if isinstance(inner_field, StructField):
                model.__init_struct_field(inner_name, inner_field)
            else:
                setattr(model, inner_name, inner_field)
        setattr(self, name, model)

    def from_dict(self, data):
        for name, value in data.items():
            if isinstance(value, dict):
                model = Model()
                model.from_dict(value)
                value = model
            setattr(self, name, value)

    def __repr__(self):
        address = hex(id(self))
        classname = self.__class__.__name__
        attrs = {}
        for name, field in self.fields.items():
            attrs[name] = self.__dict__.get(name)
        return '<{0} {1}>({2})'.format(classname, address, attrs)

    def save(self):
        collection_name = self.collection
        save_data = self.get_save_data()
        if not self.id:
            self.storage.insert(collection_name, save_data)
        else:
            self.storage.update(collection_name, {'id': self.id}, save_data)

    def delete(self):
        self.storage.delete(self.collection, {'id': self.id})
