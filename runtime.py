from collections import deque
from instruction import InstructionFactory
from error import Error
from instruction import *
from os import environ
import os
from frame import Frame, FrameHolder


class Runtime:
    _instance = None

    def __init__(self, input):
        if not self._is_initialized:

            self.frames = FrameHolder()

            self.labels = {}

            self.call_stack = deque()
            self.data_stack = deque()

            self.instruction_pointer = 0
            if input == "stdin":
                self.input = sys.stdin
            else:
                try:
                    self.input = open(input, "r")
                except:
                    exit_with_error(Error.InvalidFile)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Runtime, cls).__new__(cls)
            cls._instance._is_initialized = False

        return cls._instance

    def __del__(self):
        try:
            self.input.close()
        except AttributeError:
            pass

    def run(self, instructions):
        for idx, instruction in enumerate(instructions):
            if isinstance(instruction, Label):
                if instruction.element[0].text in self.labels:
                    exit_with_error(Error.InvalidSemantics)
                self.labels[instruction.element[0].text] = idx

        while (self.instruction_pointer < len(instructions)):
            instructions[self.instruction_pointer].execute()
            self.instruction_pointer += 1
            if environ.get("DEBUG") == "1":
                print(self.frames)
