from dataclasses import dataclass
from typing import Optional, Tuple, Sequence


@dataclass
class User:
    id: int
    user_id: int
    first_name: str
    last_name: str
    username: str
    language_code: str
    bot_name: Optional[str] = None
    token: Optional[str] = None
    is_bot: Optional[bool] = False
    webhook_url: Optional[str] = None

    @property
    def title(self):
        if self.is_bot:
            return f'BOT: {self.bot_name}'
        return f'{self.first_name.capitalize()} {self.last_name.capitalize()}'


@dataclass
class Chat:
    chat_id: int
    members: Tuple[User]

    def __init__(self, chat_id: int, members: Sequence[dict]):
        self.chat_id = chat_id
        self.members = tuple(User(**member_data) for member_data in members)