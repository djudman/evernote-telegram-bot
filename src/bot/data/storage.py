class Storage:
    def insert(self, data):
        pass

    def update(self, query, data):
        pass

    def delete(self, query):
        pass

    def find(self, query):
        pass

    def get(self, classObject, query):
        if not isinstance(query, dict):
            query = { 'id': query }
        result = self.find(query)
        return next(iter(result))

    def create_model(self, model_class, data):
        model = model_class(data)
        model.storage = self
        return model


class MongoStorage:
    pass


class MemoryStorage:
    pass
