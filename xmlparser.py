import xml.etree.ElementTree as ET
from sys import stdin, exit
from error import Error, exit_with_error


class XmlParser:
    def __init__(self, stream_type: str):
        self._stream = stream_type

    def parse_input(self) -> ET.Element:
        input = ""
        if self._stream == "stdin":
            input = stdin.read()

            try:
                root = ET.fromstring(input)
                return root
            except ET.ParseError:
                exit_with_error(Error.InvalidXmlFormat)

        else:
            try:
                return ET.parse(self._stream).getroot()
            except ET.ParseError:
                exit_with_error(Error.InvalidXmlFormat)
            except FileNotFoundError:
                exit_with_error(Error.InvalidFile)
