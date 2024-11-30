from abc import ABC, abstractmethod
from typing import Generator

from structure import Translatable


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, input_filename: str) -> Generator[Translatable, None, None]:
        pass
