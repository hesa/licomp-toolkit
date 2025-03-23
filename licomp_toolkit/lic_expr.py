import json 

import logging
from license_expression import get_spdx_licensing
from licomp_toolkit.toolkit import LicompToolkit
from licomp.interface import UseCase
from licomp.interface import Provisioning

AND = "AND"
OR = "OR"

class LicenseExpressionParser():

    def __init__(self):
        self.licensing = get_spdx_licensing()

        self.CLOSE_PARENTHESIS = ")"
        self.LICENSE_SYMBOL = "LicenseSymbol"
        self.LICENSE_WITH_SYMBOL = "LicenseWithExceptionSymbol"

    def parse_license_expression(self, expression):
        print(" ---------------------- " + expression + "-------------------------")
        p = self.__parse_expression(self.licensing.parse(expression).pretty().replace('\n',' '))
        print(" ---------------------- " + expression + "------------------------->> \n" + json.dumps(p, indent=4))
        return p

    def __is_license_with_exception(self, expression):
        return expression.strip().startswith(self.LICENSE_WITH_SYMBOL)

    def __is_license(self, expression, with_exception=False):
        if with_exception:
            return expression.strip().startswith(self.LICENSE_SYMBOL) or expression.strip().startswith(self.LICENSE_WITH_SYMBOL)
        return expression.strip().startswith(self.LICENSE_SYMBOL)

    def __is_operator(self, expression):
        return expression.startswith(AND) or expression.startswith(OR)

    def __get_operator(self, expression):
        if expression.startswith(AND):
            return AND
        if expression.startswith(OR):
            return OR
        raise Exception("BAD EXPRESSION----")

    def __get_operands_string(self, expression):
        # length of the operator and parenthesis
        op = self.__get_operator(expression)
        op_size = len(op) + 1

        # nr characters until closing (operator) parenthesis
        left_parens = 1
        operand_size = 1
        print("identify idx: " + expression[op_size:])
        for c in expression[op_size:]:
            #print("at " + c + ": " + str(operand_size))
            operand_size += 1
            if c == '(':
                left_parens += 1
            elif c == ')':
                left_parens -= 1

            if left_parens == 0:
                break

        rest = expression[op_size:operand_size+1]
        remains = expression[operand_size-1]
        print("expression : " + expression)
        print("operands   : " + rest)
        print("remains    : " + remains)
        return rest, remains
    
    def is_close(self, expression):
        return expression.startswith(CLOSE_PARENTHESIS)

    def __cleanup_license(self, operand):
        stripped_operand=operand.strip()
        print("OPERself.AND: " + operand)

        if self.__is_license_with_exception(operand):
            trimmed_operand = stripped_operand.replace(f"{self.LICENSE_WITH_SYMBOL}('", '', 1)
        else:
            trimmed_operand = stripped_operand.replace(f"{self.LICENSE_SYMBOL}('", '', 1)
    #    print("TRIMMED: " + trimmed_operand)
        closing_paren_index = trimmed_operand.find(")")
        #print("    CLEANEDUP op:  >" + operand + "<")
        print("    CLEANEDUP to:  >" + trimmed_operand + "<")
        print("    CLEANEDUP idx: " + str(closing_paren_index))
        op = trimmed_operand[:closing_paren_index-1]
        remains = trimmed_operand[closing_paren_index+1:].strip()
        print("    CLEANEDUP rem:>" + remains)
        if remains.startswith(","):
            remains = remains[1:]
        print("    CLEANEDUP op:  " + op)
        print("    CLEANEDUP rem:>" + remains + "<")
        return op, remains.strip()

    def __parse_expression(self, expression):
        print("pe: " + expression)

        if self.__is_operator(expression):
            operator = self.__get_operator(expression)
            operands = []
            print("GETTING OPERself.ANDS FROM: " + expression)
            ops, remains = self.__get_operands_string(expression)

            while ops != "":
                print("PARSE:  " + ops)
                print("PARSE:  " + ops.strip())
                if self.__is_license(ops.strip(), with_exception=True):
                    operand, rem = self.__cleanup_license(ops)
                    operands.append({
                        "type": "license",
                        "license": operand,
                    })
                    ops = rem

                elif self.__is_operator(ops.strip()):
                    operand = self.__parse_expression(ops.strip())
                    operands.append(operand)
                    print("OP ADD: " + str(operand))
                    ops = ""

                else:
                    print("uh oh ... " + str(ops))
                    import sys
                    sys.exit(1)
            print("OP RET: " + str(operand))
            return {
                "type": "operator",
                "operator": operator,
                "operands": operands,
            }

        elif self.__is_license(expression, with_exception=True):
            # TODO: what if exception???
            cleaned_up, rem = self.__cleanup_license(expression.strip())

            return {
                "type": "license",
                "license": cleaned_up,
            }

        elif self.__is_close(expression):
            print("op <--- CLOSE")
            return ""

        raise Exception("Bottom reached")


