from argument_parser import ArgumentParser
from instruction import InstructionFactory
from xmlparser import XmlParser
from error import Error, exit_with_error
from runtime import Runtime
import sys


def validate_children(children):
    orders = []
    for child in children:
        if not child.attrib.get("order", None):
            exit_with_error(Error.InvalidXmlStructure)
        try:
            order = int(child.attrib["order"])
        except:
            exit_with_error(Error.InvalidXmlStructure)

        if order <= 0:
            exit_with_error(Error.InvalidXmlStructure)

        if order in orders:
            exit_with_error(Error.InvalidXmlStructure)

        if child.tag != "instruction":
            exit_with_error(Error.InvalidXmlStructure)
        
        orders.append(order)

    try:
        children = sorted(children, key=lambda x: int(x.attrib["order"]))
    except KeyError:
        pass

    return children


if __name__ == "__main__":
    argparser = ArgumentParser()
    args = argparser.parse_args()

    xmlparser = XmlParser(args.source)
    xmlroot = xmlparser.parse_input()

    runtime = Runtime(args.input)

    instructions = validate_children(list(xmlroot))


    instructions = [InstructionFactory.create_instruction(
        elem, runtime) for elem in instructions]

    runtime.run(instructions)
