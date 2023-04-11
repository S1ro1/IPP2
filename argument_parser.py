import argparse
from error import Error, exit_with_error
import sys


class ArgumentParser:
    def __init__(self):
        self._parser = argparse.ArgumentParser(add_help=True)

    def validate_args(self, args: argparse.Namespace):
        if args.source and not args.input:
            args.input = "stdin"
        elif not args.source and args.input:
            args.source = "stdin"
        elif not args.source and not args.input:
            exit_with_error(Error.MissingArguments)
        
        return args

    def parse_args(self) -> argparse.Namespace:
        self._parser.add_argument("--source", action='store')
        self._parser.add_argument("--input", action='store')

        args = self._parser.parse_args()

        return self.validate_args(args)
