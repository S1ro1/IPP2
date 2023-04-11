import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
import sys
from error import Error, exit_with_error
from frame import Frame
import re


class Nil:
    def __init__(self):
        pass

    def __str__(self):
        return "nil"
    
    def __eq__(self, __value: object) -> bool:
        return type(__value) is Nil

class Undefined:
    def __init__(self):
        pass


class Instruction(ABC):

    def __init__(self, element, runtime):
        self.element = element
        self.runtime = runtime

    @abstractmethod
    def execute(self):
        pass

    def parse_symbol(self, element):
        if element.attrib.get("type") == "var":
            return self.parse_var(element)

        if element.attrib.get("type") == "int":
            try:
                x = int(element.text, base=0)
            except:
                exit_with_error(Error.InvalidXmlStructure)
            return x

        if element.attrib.get("type") == "bool":
            if element.text == "false":
                return False
            else:
                return True

        if element.attrib.get("type") == "string":
            try:
                x = re.sub(r"\\([0-9]{3})",
                        lambda x: chr(int(x.group(1))), element.text)
            except:
                x = ""

            return x

        if element.attrib.get("type") == "nil":
            return Nil()

    def parse_type(self, element):
        if element.attrib.get("type") != "type":
            exit_with_error(Error.InvalidXmlStructure)

        if element.text not in ["int", "bool", "string", "nil"]:
            exit_with_error(Error.InvalidOperands)

        return element.text

    def parse_var(self, element):
        splittext = element.text.split("@")
        if len(splittext) != 2:
            exit_with_error(Error.InvalidXmlStructure)

        if splittext[0] not in self.runtime.frames:
            exit_with_error(Error.InvalidFrame)

        return splittext[0], splittext[1]

    def parse_label(self, element):
        return element.text


class Move(Instruction):
    def execute(self):
        if len(self.element) != 2:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")

        if arg1 is None or arg2 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)

        if type(arg2) is tuple:
            source_frame, source_name = arg2
            self.runtime.frames[target_frame].update(
                target_name, self.runtime.frames[source_frame][source_name])
        else:
            self.runtime.frames[target_frame].update(target_name, arg2)


class CreateFrame(Instruction):
    def execute(self):
        if len(self.element) != 0:
            exit_with_error(Error.InvalidXmlStructure)

        self.runtime.frames["TF"] = Frame()


class PushFrame(Instruction):
    def execute(self):
        if len(self.element) != 0:
            exit_with_error(Error.InvalidXmlStructure)

        self.runtime.frames["LF"].append(self.runtime.frames["TF"])
        self.runtime.frames["TF"] = None


class PopFrame(Instruction):
    def execute(self):
        if len(self.element) != 0:
            exit_with_error(Error.InvalidXmlStructure)

        try:
            self.runtime.frames["TF"] = self.runtime.frames["LF"].pop()
        except:
            exit_with_error(Error.InvalidFrame)


class DefVar(Instruction):
    def execute(self):
        if len(self.element) != 1:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        if arg1 is None:
            exit_with_error(Error.InvalidXmlStructure)
        source_frame, source_name = self.parse_var(arg1)

        if source_name not in self.runtime.frames[source_frame]:
            self.runtime.frames[source_frame][source_name] = None
        else:
            exit_with_error(Error.InvalidSemantics)


class Call(Instruction):
    def execute(self):
        if len(self.element) != 1:
            exit_with_error(Error.InvalidXmlStructure)

        self.runtime.call_stack.append(self.runtime.instruction_pointer)

        label_name = self.parse_label(self.element.find("arg1"))

        for label in self.runtime.labels:
            if label == label_name:
                self.runtime.instruction_pointer = self.runtime.labels[label]
                return

        exit_with_error(Error.InvalidSemantics)


class Return(Instruction):
    def execute(self):
        if len(self.element) != 0:
            exit_with_error(Error.InvalidXmlStructure)

        if len(self.runtime.call_stack) == 0:
            sys.exit(Error.MissingValue)
        else:
            self.runtime.instruction_pointer = self.runtime.call_stack.pop()


class Pushs(Instruction):
    def execute(self):
        if len(self.element) != 1:
            exit_with_error(Error.InvalidXmlStructure)

        arg = self.element.find("arg1")
        arg = self.parse_symbol(arg)

        if type(arg) is tuple:
            val = self.runtime.frames[arg[0]][arg[1]]
        else:
            val = arg

        self.runtime.data_stack.append(val)


class Pops(Instruction):
    def execute(self):
        if len(self.element) != 1:
            exit_with_error(Error.InvalidXmlStructure)
        arg = self.element.find("arg1")

        target_frame, target_name = self.parse_var(arg)

        if len(self.runtime.data_stack) == 0:
            exit_with_error(Error.MissingValue)

        self.runtime.frames[target_frame].update(
            target_name, self.runtime.data_stack.pop())


class Add(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if not type(arg2) is int or not type(arg3) is int:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 + arg3)


class Sub(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if not type(arg2) is int or not type(arg3) is int:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 - arg3)


class Mul(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if not type(arg2) is int or not type(arg3) is int:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 * arg3)


class Idiv(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if not type(arg2) is int or not type(arg3) is int:
            exit_with_error(Error.InvalidOperands)

        if arg3 == 0:
            exit_with_error(Error.InvalidOperandValue)
        self.runtime.frames[target_frame].update(target_name, arg2 // arg3)


class Lt(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not type(arg3):
            exit_with_error(Error.InvalidOperands)

        if type(arg2) is Nil or type(arg2) is Nil:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 < arg3)


class Gt(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not type(arg3):
            exit_with_error(Error.InvalidOperands)

        if type(arg2) is Nil or type(arg2) is Nil:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 > arg3)


class Eq(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not type(arg3):
            if type(arg2) is Nil or type(arg3) is Nil:
                pass
            else:
                exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 == arg3)


class And(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not bool or type(arg3) is not bool:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 and arg3)


class Or(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]
        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not bool or type(arg3) is not bool:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 or arg3)


class Not(Instruction):
    def execute(self):
        if len(self.element) != 2:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")

        if arg1 is None or arg2 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg2) is not bool:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, not arg2)


class Int2Char(Instruction):
    def execute(self):
        if len(self.element) != 2:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")

        if arg1 is None or arg2 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg2) is not int:
            exit_with_error(Error.InvalidOperands)

        try:
            self.runtime.frames[target_frame].update(target_name, chr(arg2))
        except ValueError:
            exit_with_error(Error.InvalidStringOperation)


class Stri2Int(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not str or type(arg3) is not int:
            exit_with_error(Error.InvalidOperands)
        
        if arg3 >= len(arg2) or arg3 < 0:
            exit_with_error(Error.InvalidStringOperation)

        self.runtime.frames[target_frame].update(target_name, ord(arg2[arg3]))


class Read(Instruction):
    def execute(self):
        if len(self.element) != 2:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")

        if arg1 is None or arg2 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)
        _type = self.parse_type(arg2)

        val = self.runtime.input.readline()

        if val == "":
            val = Nil()
        else:
            val = val.rstrip('\n')

            if val == "" and _type != "string":
                val = Nil()
            
            elif _type == "int":
                try:
                    val = int(val, 0)
                except ValueError:
                    val = Nil()
                    
            elif _type == "bool":
                if val.lower() == "true":
                    val = True
                else:
                    val = False

            elif _type == "string":
                if val == "true\n":
                    val = True

            elif _type == "nil":
                exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, val)


class Write(Instruction):
    def execute(self):
        if len(self.element) != 1:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")

        if arg1 is None:
            exit_with_error(Error.InvalidXmlStructure)

        val = self.parse_symbol(arg1)

        if type(val) is tuple:
            val = self.runtime.frames[val[0]][val[1]]

        if type(val) is Nil:
            val = ""
        if type(val) is bool:
            val = str(val).lower()

        print(val, end="")


class Concat(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not str or type(arg3) is not str:
            exit_with_error(Error.InvalidOperands)

        self.runtime.frames[target_frame].update(target_name, arg2 + arg3)


class Strlen(Instruction):
    def execute(self):
        if len(self.element) != 2:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")

        if arg1 is None or arg2 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg2) is not str:
            exit_with_error(Error.InvalidOperands)
        

        self.runtime.frames[target_frame].update(target_name, len(arg2))


class GetChar(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) is not str or type(arg3) is not int:
            exit_with_error(Error.InvalidOperands)

        if arg3 >= len(arg2) or arg3 < 0:
            exit_with_error(Error.InvalidStringOperation)

        if arg2[arg3] == "":
            exit_with_error(Error.InvalidStringOperation)

        self.runtime.frames[target_frame].update(target_name, arg2[arg3])


class SetChar(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)
        val = self.runtime.frames[target_frame][target_name]

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]][0]

        if type(val) is not str or type(arg2) is not int or type(arg3) is not str:
            exit_with_error(Error.InvalidOperands)

        if arg2 >= len(val) or arg2 < 0:
            exit_with_error(Error.InvalidStringOperation)

        if arg3 == "" or val == "":
            exit_with_error(Error.InvalidStringOperation)

        val = val[:arg2] + arg3[0] + val[arg2 + 1:]

        self.runtime.frames[target_frame].update(target_name, val)


class Type(Instruction):
    def execute(self):
        if len(self.element) != 2:
            exit_with_error(Error.InvalidXmlStructure)
        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")

        if arg1 is None or arg2 is None:
            exit_with_error(Error.InvalidXmlStructure)

        target_frame, target_name = self.parse_var(arg1)

        arg2 = self.parse_symbol(arg2)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]].get(arg2[1], Undefined)
        
        if arg2 is Undefined:
            exit_with_error(Error.InvalidVariable)
        
        if type(arg2) is int:
            val = "int"
        if type(arg2) is bool:
            val = "bool"
        if type(arg2) is str:
                val = "string"
        if type(arg2) is Nil:
            val = "nil"

        if arg2 is None:
            val = ""

        self.runtime.frames[target_frame].update(target_name, val)


class Label(Instruction):
    def execute(self):
        if len(self.element) != 1:
            exit_with_error(Error.InvalidXmlStructure)
        pass


class Jump(Instruction):
    def execute(self):
        if len(self.element) != 1:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")

        if arg1 is None:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.parse_label(arg1)

        if arg1 not in self.runtime.labels:
            exit_with_error(Error.InvalidSemantics)

        self.runtime.instruction_pointer = self.runtime.labels[arg1]


class JumpIfEq(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.parse_label(arg1)

        if arg1 not in self.runtime.labels:
            exit_with_error(Error.InvalidSemantics)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        if type(arg2) != type(arg3):
            if type(arg2) is Nil or type(arg3) is Nil:
                pass
            else:
                exit_with_error(Error.InvalidOperands)

        if arg2 == arg3:
            self.runtime.instruction_pointer = self.runtime.labels[arg1]


class JumpIfNeq(Instruction):
    def execute(self):
        if len(self.element) != 3:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.element.find("arg1")
        arg2 = self.element.find("arg2")
        arg3 = self.element.find("arg3")

        if arg1 is None or arg2 is None or arg3 is None:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.parse_label(arg1)

        if arg1 not in self.runtime.labels:
            exit_with_error(Error.InvalidSemantics)

        arg2 = self.parse_symbol(arg2)
        arg3 = self.parse_symbol(arg3)

        if type(arg2) is tuple:
            arg2 = self.runtime.frames[arg2[0]][arg2[1]]

        if type(arg3) is tuple:
            arg3 = self.runtime.frames[arg3[0]][arg3[1]]

        # if type(arg2) is Nil or type(arg3) is Nil:
        #     if not (type(arg2) is Nil and type(arg3) is Nil):
        #         self.runtime.instruction_pointer = self.runtime.labels[arg1]

        if type(arg2) != type(arg3):
            if type(arg2) is Nil or type(arg3) is Nil:
                pass
            else:
                exit_with_error(Error.InvalidOperands)

        if arg2 != arg3:
            self.runtime.instruction_pointer = self.runtime.labels[arg1]


class Exit(Instruction):
    def execute(self):
        arg1 = self.element.find("arg1")

        if arg1 is None:
            exit_with_error(Error.InvalidXmlStructure)

        arg1 = self.parse_symbol(arg1)
        if type(arg1) is tuple:
            arg1 = self.runtime.frames[arg1[0]][arg1[1]]

        if type(arg1) is not int:
            exit_with_error(Error.InvalidOperands)

        if arg1 < 0 or arg1 > 49:
            exit_with_error(Error.InvalidOperandValue)

        sys.exit(arg1)


class DPrint(Instruction):
    def execute(self):
        pass


class Break(Instruction):
    def execute(self):
        pass


class InstructionFactory:
    dispatch_dict = {
        "MOVE": Move,
        "CREATEFRAME": CreateFrame,
        "PUSHFRAME": PushFrame,
        "POPFRAME": PopFrame,
        "DEFVAR": DefVar,
        "CALL": Call,
        "RETURN": Return,
        "PUSHS": Pushs,
        "POPS": Pops,
        "ADD": Add,
        "SUB": Sub,
        "MUL": Mul,
        "IDIV": Idiv,
        "LT": Lt,
        "GT": Gt,
        "EQ": Eq,
        "AND": And,
        "OR": Or,
        "NOT": Not,
        "INT2CHAR": Int2Char,
        "STRI2INT": Stri2Int,
        "READ": Read,
        "WRITE": Write,
        "CONCAT": Concat,
        "STRLEN": Strlen,
        "GETCHAR": GetChar,
        "SETCHAR": SetChar,
        "TYPE": Type,
        "LABEL": Label,
        "JUMP": Jump,
        "JUMPIFEQ": JumpIfEq,
        "JUMPIFNEQ": JumpIfNeq,
        "EXIT": Exit,
        "DPRINT": DPrint,
        "BREAK": Break,
    }

    @classmethod
    def create_instruction(cls, element, runtime):
        try:
            return cls.dispatch_dict[element.attrib['opcode'].upper()](element, runtime)
        except KeyError:
            exit_with_error(Error.InvalidXmlStructure)
