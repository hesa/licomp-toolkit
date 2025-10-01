# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from license_expression import Licensing
from licomp.interface import LicompException
from licomp.return_codes import ReturnCodes

AND = "AND"
OR = "OR"

COMPATIBILITY_TYPE = 'compatibility_type'
COMPATIBILITY_OUTBOUND_LICENSE = 'outbound_license'
COMPATIBILITY_INBOUND_LICENSE = 'inbound_license'

class LicenseExpressionParser():

    def __init__(self):
        self.licensing = Licensing([])

        self.CLOSE_PARENTHESIS = ")"
        self.LICENSE_SYMBOL = "LicenseSymbol"
        self.LICENSE_WITH_SYMBOL = "LicenseWithExceptionSymbol"

    def parse_license_expression(self, expression):
        if not expression:
            raise LicompException("No license provided: " + str(expression), ReturnCodes.LICOMP_PARSE_ERROR)
        p = self.__parse_expression(self.licensing.parse(expression).pretty().replace('\n', ' '))
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
        for c in expression[op_size:]:
            operand_size += 1
            if c == '(':
                left_parens += 1
            elif c == ')':
                left_parens -= 1

            if left_parens == 0:
                break

        rest = expression[op_size:operand_size + 1]
        remains = expression[operand_size + 4:]
        return rest, remains

    def is_close(self, expression):
        return expression.startswith(self.CLOSE_PARENTHESIS)

    def __cleanup_license(self, operand):
        stripped_operand = operand.strip()

        if self.__is_license_with_exception(operand):
            trimmed_operand = stripped_operand.replace(f"{self.LICENSE_WITH_SYMBOL}('", '', 1)
        else:
            trimmed_operand = stripped_operand.replace(f"{self.LICENSE_SYMBOL}('", '', 1)
        closing_paren_index = trimmed_operand.find(")")
        op = trimmed_operand[:closing_paren_index - 1]
        remains = trimmed_operand[closing_paren_index + 1:].strip()
        if remains.startswith(","):
            remains = remains[1:]
        return op, remains.strip()

    def __parse_expression(self, expression):
        logging.debug(f'__parse_expression: {expression}')

        if self.__is_operator(expression):
            operator = self.__get_operator(expression)
            operands = []
            ops, remains = self.__get_operands_string(expression)
            while ops != "":
                if self.__is_license(ops.strip(), with_exception=True):
                    operand, rem = self.__cleanup_license(ops)
                    operands.append({
                        COMPATIBILITY_TYPE: "license",
                        'license': operand,
                    })
                    ops = rem

                elif self.__is_operator(ops.strip()):
                    operand = self.__parse_expression(ops.strip())
                    _ops, _remains = self.__get_operands_string(ops.strip())
                    operands.append(operand)
                    ops = _remains

                else:
                    raise LicompException(f'Failed parsing expression "{ops}". Complete expression "{expression}"', ReturnCodes.LICOMP_PARSE_ERROR)
            return {
                COMPATIBILITY_TYPE: 'expression',
                "operator": operator,
                "operands": operands,
            }

        elif self.__is_license(expression, with_exception=True):
            cleaned_up, rem = self.__cleanup_license(expression.strip())
            return {
                COMPATIBILITY_TYPE: "license",
                'license': cleaned_up,
            }

        elif self.__is_close(expression):
            return ""

        raise Exception("Bottom reached")

    def to_string(self, parsed_license):
        license_type = parsed_license['compatibility_type']
        if license_type == 'license':
            return parsed_license['license']

        operator = parsed_license['operator']
        license_expression = []
        for operand in parsed_license['operands']:
            license_expression.append(f' ( {self.to_string(operand)} ) ')
        return str(self.licensing.parse(operator.join(license_expression)))
