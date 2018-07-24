from importlib import import_module


class Storage:
    def __init__(self, provider, model_class):
        self.provider = provider
        self.model_class = model_class
        if hasattr(model_class, 'config'):
            self.db = model_class.config.get('db')
            self.collection = model_class.config.get('collection')

    def get(self, query):
        if not isinstance(query, dict):
            query = {'id': query}
        data = self.provider.get(query)
        if data:
            return self.model_class(data, storage=self)

    def get_all(self, query, sort=None):
        documents = self.provider.get_all(query, sort=sort)
        models = []
        for data in documents:
            model = self.model_class(data)
            models.append(model)
        return models

    def create_model(self, data):
        return self.model_class(data, storage=self)

    def count(self, query):
        return self.provider.count(query)

    def __repr__(self):
        return '{0}({1}, {2})'.format(
            self.__class__.__name__,
            self.provider.__class__.__name__,
            self.model_class.__name__,
        )


class StorageMixin:
    def __init__(self, *args, **kwargs):
        self._storage_cache = {}
        self.config = kwargs.get('config')

    def get_storage(self, model_class):
        cache_key = model_class.__name__
        if not self._storage_cache.get(cache_key):
            model_config = getattr(model_class, 'config', {})
            provider_name = model_config.get('provider')
            if provider_name:
                provider_config = self.config['storage']['providers'][provider_name]
            else:
                for name, config in self.config['storage']['providers'].items():
                    if config.get('default'):
                        provider_config = config
                        break
            if not provider_config:
                raise Exception('Provider not configured.')
            parts = provider_config['class'].split('.')
            classname = parts[-1]
            module_name = '.'.join(parts[:-1])
            module = import_module(module_name)
            ProviderClass = getattr(module, classname)
            provider = ProviderClass({
                'db': model_config.get('db', provider_config.get('db')),
                'collection': model_config.get('collection'),
                'connection_string': provider_config.get('connection_string'),
            })
            storage = Storage(provider, model_class)
            self._storage_cache[cache_key] = storage
        return self._storage_cache[cache_key]
