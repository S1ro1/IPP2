import sys
from error import exit_with_error, Error
from collections import deque


class Frame:
    def __init__(self):
        self.collection = {}

    def __getitem__(self, key):
        if key not in self.collection:
            exit_with_error(Error.InvalidVariable)

        val = self.collection[key]

        if val is None:
            exit_with_error(Error.MissingValue)

        return val

    def __setitem__(self, key, value):
        self.collection[key] = value

    def __repr__(self) -> str:
        return str(self.collection)

    def __contains__(self, key):
        return key in self.collection

    def get(self, key, default=None):
        return self.collection.get(key, default)

    def update(self, name, value):
        if name not in self.collection:
            exit_with_error(Error.InvalidVariable)

        self.collection[name] = value


class LocalFrame:
    def __init__(self):
        self.collection = deque()

    def __getitem__(self, key):
        if not self.collection:
            exit_with_error(Error.InvalidFrame)

        if key not in self.collection[-1]:
            exit_with_error(Error.InvalidVariable)

        val = self.collection[-1][key]

        if val is None:
            exit_with_error(Error.MissingValue)

        return val

    def __setitem__(self, key, value):
        if not self.collection:
            exit_with_error(Error.InvalidFrame)
        self.collection[-1][key] = value

    def __contains__(self, key):
        if not self.collection:
            exit_with_error(Error.InvalidFrame)
        return key in self.collection[-1]

    def get(self, key, default=None):
        if not self.collection:
            exit_with_error(Error.InvalidFrame)
        return self.collection[-1].get(key, default)

    def update(self, name, value):
        if not self.collection:
            exit_with_error(Error.InvalidFrame)
        if name not in self.collection[-1]:
            exit_with_error(Error.InvalidVariable)

        self.collection[-1][name] = value

    def pop(self):
        return self.collection.pop()

    def append(self, frame):
        self.collection.append(frame)


class FrameHolder:
    def __init__(self):
        self.collection = {
            "GF": Frame(),
            "LF": LocalFrame(),
            "TF": None,
        }

    def __getitem__(self, key):
        if self.collection.get(key, None) is None:
            exit_with_error(Error.InvalidFrame)

        return self.collection[key]

    def __repr__(self) -> str:
        return str(self.collection)

    def __setitem__(self, key, value):
        self.collection[key] = value

    def __contains__(self, key):
        if key not in self.collection:
            exit_with_error(Error.InvalidFrame)
        return key in self.collection

    def get(self, key, default=None):
        return self.collection.get(key, default)
