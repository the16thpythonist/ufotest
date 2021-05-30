import functools
from typing import Callable
from abc import abstractmethod

from ufotest.config import Config
from ufotest.plugin import PluginManager


class AbstractHook:

    def __init__(self, hook_name: str, priority: int, config=Config()):
        self.hook_name = hook_name
        self.priority = priority
        self.config = config

    @abstractmethod
    def __call__(self, func: Callable):
        raise NotImplemented()


class Filter(AbstractHook):

    def __call__(self, func: Callable):
        self.config.pm.register_filter(self.hook_name, func, self.priority)
        return func


class Action(AbstractHook):

    def __call__(self, func: Callable):
        self.config.pm.register_action(self.hook_name, func, self.priority)
        return func


