"""
"""
from abc import ABC, abstractclassmethod


class StrategiesAbstract(ABC):
    @abstractclassmethod
    def create_dictionary_for_db(cls):
        raise NotImplementedError
        pass
    @abstractclassmethod
    def print_details(cls):
        raise NotImplementedError
        pass
    @abstractclassmethod
    def initialize(cls):
        raise NotImplementedError
        pass
    @abstractclassmethod
    def check_execution(cls):
        raise NotImplementedError
        pass
    @abstractclassmethod
    def refresh(cls):
        raise NotImplementedError
        pass

