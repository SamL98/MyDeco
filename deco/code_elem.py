from abc import ABC, abstractmethod

class CodeElement(object):
    @abstractmethod
    def branches(self):
        raise NotImplementedError()

    @abstractmethod
    def branches(self):
        raise NotImplementedError()

    @abstractmethod
    def terminates(self):
        # As in is a block terminator. TODO: Fix this terminology.
        raise NotImplementedError()

    @abstractmethod
    def is_conditional(self):
        raise NotImplementedError()

    @abstractmethod
    def is_indirect(self):
        raise NotImplementedError()

    @abstractmethod
    def target(self):
        raise NotImplementedError()

    @abstractmethod
    def fallthrough(self):
        raise NotImplementedError()
