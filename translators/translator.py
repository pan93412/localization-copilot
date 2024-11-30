from abc import ABC, abstractmethod

from structure import Translatable, Translation


class BaseTranslator(ABC):
    @abstractmethod
    async def translate(self, translatable: Translatable) -> Translation:
        pass
