# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from license_expression import get_spdx_licensing
from licomp_toolkit.toolkit import LicompToolkit
from licomp.interface import UseCase
from licomp.interface import Provisioning

AND = "AND"
OR = "OR"

COMPATIBILITY_TYPE = 'compatibility_type'
COMPATIBILITY_OUTBOUND_LICENSE = 'outbound_license'
COMPATIBILITY_INBOUND_LICENSE = 'inbound_license'

class LicenseExpressionParser():

    def __init__(self):
        self.licensing = get_spdx_licensing()

        self.CLOSE_PARENTHESIS = ")"
        self.LICENSE_SYMBOL = "LicenseSymbol"
        self.LICENSE_WITH_SYMBOL = "LicenseWithExceptionSymbol"

    def parse_license_expression(self, expression):
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
        remains = expression[operand_size - 1]
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
                    operands.append(operand)
                    ops = ""

                else:
                    print("uh oh ... " + str(ops))
                    import sys
                    sys.exit(1)
            return {
                COMPATIBILITY_TYPE: "operator",
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

class LicenseExpressionChecker():

    def outbound_inbound_compatibility(self, outbound, lic):
        licomp = LicompToolkit()
        return licomp.outbound_inbound_compatibility(outbound,
                                                     lic,
                                                     usecase="library",
                                                     provisioning="binary-distribution")

    def __compatibility_status(self, compatibility):
        status = compatibility['summary']['results']

        rets = []
        for ret in status:
            if ret == 'nr_valid':
                continue
            rets.append(ret)

        if len(rets) == 1:
            return rets[0]

        return "yes"

    def check_compatibility(self, outbound, parsed_expression, detailed_report=False):
        compat_object = {
            COMPATIBILITY_TYPE: parsed_expression[COMPATIBILITY_TYPE],
            'compatiblity_check': 'outbound-operator -> inbound-license',
        }

        if parsed_expression[COMPATIBILITY_TYPE] == 'license':
            compat_object['compatiblity_check'] = 'outbound-license -> inbound-license'
            lic = parsed_expression['license']
            compat = self.outbound_inbound_compatibility(outbound, lic)
            compat_object['compatibility'] = self.__compatibility_status(compat)
            if detailed_report:
                compat_object['compatibility_details'] = compat

            compat_object['inbound_license'] = lic
            compat_object['outbound_license'] = outbound

        else:
            operator = parsed_expression['operator']
            operands = parsed_expression['operands']
            compat_object['compatibility_object'] = {
                'operator': operator,
                'operands': [],
            }

            operands_object = []
            for operand in operands:
                operand_compat = self.check_compatibility(outbound, operand, detailed_report=detailed_report)
                operand_object = {
                    'compatibility_object': operand_compat,
                    'compatibility': operand_compat['compatibility'],
                }
                operands_object.append(operand_object)

            compat_object['compatibility'] = self.summarise_compatibilities(operator, operands_object)
            compat_object['compatibility_object']['operands'] = operands_object

        return compat_object

    def __init_summary(self, operands):
        summary = {
            "yes": 0,
            "no": 0,
            "depends": 0,
            "unknown": 0,
        }
        for operand in operands:
            compat = operand['compatibility']
            summary[compat] = summary[compat] + 1
        return summary

    def __summarise_compatibilities_and(self, operands):
        nr_operands = len(operands)
        summary = self.__init_summary(operands)

        if summary['no'] != 0:
            return 'no'

        if summary['yes'] == nr_operands:
            return "yes"

        return "no"

    def __summarise_compatibilities_or(self, operands):
        summary = self.__init_summary(operands)

        if summary['yes'] != 0:
            return 'yes'

        return "no"

    def summarise_compatibilities(self, operator, operands):
        return {
            AND: self.__summarise_compatibilities_and,
            OR: self.__summarise_compatibilities_or,
        }[operator](operands)

class _OBSOLETE_ExpressionExpressionChecker():

    def __init__(self):
        self.le_checker = LicenseExpressionChecker()
        self.le_parser = LicenseExpressionParser()

    def __parsed_expression_to_name(self, parsed_expression):
        return parsed_expression[parsed_expression[COMPATIBILITY_TYPE]]

    def check_compatibility(self, outbound, inbound, usecase, provisioning, detailed_report=False):
        inbound_parsed = self.le_parser.parse_license_expression(inbound)

        outbound_parsed = self.le_parser.parse_license_expression(outbound)

        compatibility_report = self.__check_compatibility(outbound_parsed,
                                                          inbound_parsed,
                                                          usecase,
                                                          provisioning,
                                                          detailed_report)

        return {
            'inbound': inbound,
            'outbound': outbound,
            'usecase': UseCase.usecase_to_string(usecase),
            'provisioning': Provisioning.provisioning_to_string(provisioning),
            'compatibility': compatibility_report['compatibility'],
            'compatibility_type': compatibility_report['compatibility_type'],
            'compatibility_check': f'outbound-{compatibility_report["compatibility_type"]} -> inbound-{inbound_parsed["compatibility_type"]}',
            'compatibility_report': compatibility_report,
        }

    def __check_compatibility(self, outbound_parsed, inbound_parsed, usecase, provisioning, detailed_report=False):

        outbound_type = outbound_parsed[COMPATIBILITY_TYPE]
        compat_object = {
            COMPATIBILITY_TYPE: outbound_type,
            'inbound_license': self.le_parser.to_string(inbound_parsed),
            'outbound_license': self.le_parser.to_string(outbound_parsed),
        }

        if outbound_type == 'license':
            compat_object['compatiblity_check'] = f'outbound-license -> inbound-{inbound_parsed["compatibility_type"]}'
            outbound_parsed_license = outbound_parsed['license']
            # Check if:
            #    outbound license
            #    is compatible with
            #    inbound license
            compat = self.le_checker.check_compatibility(outbound_parsed_license,
                                                         inbound_parsed,
                                                         detailed_report)
            compat_object['compatibility'] = compat['compatibility']
            compat_object['compatibility_details'] = compat

        elif outbound_type == 'operator':
            compat_object['compatiblity_check'] = f'outbound-operator -> inbound-{inbound_parsed["compatibility_type"]}'
            operator = outbound_parsed['operator']
            operands = outbound_parsed['operands']

            compat_object['compatibility_object'] = {
                'operator': operator,
                'operands': [],
            }

            operands_object = []
            for operand in operands:
                # Check if:
                #    operand from outbound license
                #    is compatible with
                #    inbound license
                operand_compat = self.__check_compatibility(operand,
                                                            inbound_parsed,
                                                            detailed_report)
                operand_object = {
                    'compatibility_object': operand_compat,
                    'compatibility': operand_compat['compatibility'],
                }
                operands_object.append(operand_object)

            compat_object['compatibility'] = self.le_checker.summarise_compatibilities(operator, operands_object)
            compat_object['compatibility_object']['operands'] = operands_object

        return compat_object
