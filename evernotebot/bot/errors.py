class EvernoteBotException(Exception):
    def __init__(self, message: str):
        super(EvernoteBotException, self).__init__()
        self.message = message
