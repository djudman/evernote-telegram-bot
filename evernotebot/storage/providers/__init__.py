import typing
from abc import ABCMeta, abstractmethod
from typing import Optional, Dict


class BaseProvider(metaclass=ABCMeta):
    @abstractmethod
    def create(self, data: dict, auto_generate_id=False):
        pass

    @abstractmethod
    def get(self, object_id: int, fail_if_not_exists: bool = False) -> Dict:
        pass

    @abstractmethod
    def get_all(self, query: Optional[Dict] = None) -> typing.Generator:
        pass

    @abstractmethod
    def save(self, data: dict) -> int:
        pass

    @abstractmethod
    def delete(self, object_id: int, check_deleted_count: bool = True) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
