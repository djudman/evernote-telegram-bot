from dataclasses import dataclass, asdict

from utelegram.models import init_dataclass_fields


@dataclass
class TelegramData:
    first_name: str
    last_name: str
    username: str
    chat_id: int


@dataclass
class EvernoteAccess:
    permission: str
    token: str = None


@dataclass
class EvernoteNotebook:
    name: str
    guid: str


@dataclass
class EvernoteOauthData:
    token: str
    secret: str
    callback_key: str
    api_key: str = None


@dataclass
class EvernoteData:
    access: EvernoteAccess
    notebook: EvernoteNotebook = None
    shared_note_id: str = None
    oauth: EvernoteOauthData = None

    def __post_init__(self):
        init_dataclass_fields(self)


@dataclass
class BotUser:
    id: int
    created: float
    last_request_ts: float
    telegram: TelegramData
    evernote: EvernoteData
    bot_mode: str = 'multiple_notes'
    state: str = None

    def __post_init__(self):
        init_dataclass_fields(self)

    def asdict(self):
        return asdict(self)
