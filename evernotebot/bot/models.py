from dataclasses import dataclass, asdict


@dataclass
class TelegramData:
    first_name: str
    last_name: str
    username: str
    chat_id: int


@dataclass
class EvernoteAccess:
    token: str
    permission: str


@dataclass
class EvernoteNotebook:
    name: str
    guid: str


@dataclass
class EvernoteOauthData:
    token: str
    secret: str
    callback_key: str
    api_key: str


@dataclass
class EvernoteData:
    access: EvernoteAccess
    notebook: EvernoteNotebook
    shared_note_id: str
    oauth: EvernoteOauthData = None


@dataclass
class BotUser:
    created: float
    last_request_ts: float
    bot_mode: str = 'multiple_notes'
    state: str = None
    telegram: TelegramData = None
    evernote: EvernoteData = None

    def asdict(self):
        return asdict(self)
