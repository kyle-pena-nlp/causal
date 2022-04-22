from abc import ABC, abstractmethod, abstractstaticmethod
from dataclasses import dataclass

@dataclass(frozen = True, eq = True)
class Expression:    

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def parse(self):
        pass

    @abstractmethod
    def hat_free(self):
        pass