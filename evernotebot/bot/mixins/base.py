class BaseMixin:
    def __init__(self, config: dict):
        self.config = config
        bot_name = config['telegram']['bot_name']
        self.url = f'https://t.me/{bot_name}'
        self.name = bot_name

    def exec_all_mixins(self, callback_name: str, *args):
        for _class in self.__class__.__bases__:
            if not hasattr(_class, callback_name):
                continue
            method = getattr(_class, callback_name)
            out = method(self, *args)
            if out is False:
                break
