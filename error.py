from enum import IntEnum
from sys import exit, stderr


class Error(IntEnum):
    MissingArguments = 10
    InvalidFile = 11
    InvalidXmlFormat = 31
    InvalidXmlStructure = 32
    InvalidSemantics = 52
    InvalidOperands = 53
    InvalidVariable = 54
    InvalidFrame = 55
    MissingValue = 56
    InvalidOperandValue = 57
    InvalidStringOperation = 58


def exit_with_error(error_code):
    exit(error_code)
