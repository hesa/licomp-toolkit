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


        
class LicenseExpressionChecker():

    def outbound_inbound_compatibility(self, outbound, lic):
        licomp = LicompToolkit()
        print("out: " + str(outbound))
        print("in:  " + str(lic))
        return licomp.outbound_inbound_compatibility(outbound,
                                                     lic,
                                                     usecase="library",
                                                     provisioning="binary-distribution")
        
    def __compatibility_status(self, compatibility):
        status = compatibility['summary']['results']
        nr_valid = status['nr_valid']

        rets = []
        for ret in status:
            if ret == 'nr_valid':
                continue
            rets.append(ret)

        print("________________________________________________status: " + str(status))
        print("________________________________________________status: " + str(rets))

        # status: {'nr_valid': '5', 'yes': {'count': 5, 'percent': 100.0}}

        if len(rets) == 1:
            print("RETURN: " + str(rets[0]))
            return rets[0]

        print("RETURN: " + str(rets))
        print("RETURN: " + str(compatibility))
        return "yes"
    
    def check_compatibility(self, outbound, parsed_expression, detailed_report=False):
        if parsed_expression['type'] == 'license':
            print(f' license: {parsed_expression}')
            lic = parsed_expression['license']
            compat = self.outbound_inbound_compatibility(outbound, lic)
            parsed_expression['compatibility'] = self.__compatibility_status(compat)
            if detailed_report:
                parsed_expression['compatibility_details'] = compat
            parsed_expression['outbound'] = outbound
            print("Added compat: " + str(compat))

            return parsed_expression
        else:
            operator = parsed_expression['operator']
            operands = parsed_expression['operands']

            for operand in operands:
                print(f'hi yall {operator}: {operand}')
                self.check_compatibility(outbound, operand, detailed_report=detailed_report)
                #compat = summarise_compatibilities(operator, operand)
                #operand['compatibility'] = "compat"
                #print("Added compat: " + str(compat))
                operand['outbound'] = outbound

            parsed_expression["outbound"] = outbound
            parsed_expression["compatibility"] = self.summarise_compatibilities(operator, operands)
            return parsed_expression
    
    def __init_summary(self, operands):
        summary = {
            "yes": 0,
            "no": 0,
            "depends": 0,
            "unknown": 0,
        }
        for operand in operands:
            print("_init_summary: " + str(operand))
            compat = operand['compatibility']
            summary[compat] = summary[compat] + 1
        return summary

    def __summarise_compatibilities_and(self, operands):
        nr_operands = len(operands)
        for operand in operands:
            print("OP: " + str(operand))
        summary = self.__init_summary(operands)
        #print(json.dumps(summary, indent=4))
        print("len: " + str(nr_operands))

        if summary['no'] != 0:
            return 'no'

        if summary['yes'] == nr_operands:
            return "yes"

        return "no"


    def __summarise_compatibilities_or(self, operands):
        nr_operands = len(operands)
        summary = self.__init_summary(operands)

        if summary['yes'] != 0:
            return 'yes'

        return "no"


    def summarise_compatibilities(self, operator, operands):
        return {
            AND: self.__summarise_compatibilities_and,
            OR: self.__summarise_compatibilities_or
        }[operator](operands)


