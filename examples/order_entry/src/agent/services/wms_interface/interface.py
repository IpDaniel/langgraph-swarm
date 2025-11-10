from abc import ABC, abstractmethod


class WMSInterface(ABC):
    @staticmethod
    @abstractmethod
    def lookup_item():
        pass