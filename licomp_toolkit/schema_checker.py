# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import jsonschema
import logging
import os

from licomp_toolkit.toolkit import LicompToolkit
from licomp.interface import LicompException

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.realpath(os.path.join(SCRIPT_DIR, "data"))
SCHEMA_FILE = os.path.realpath(os.path.join(DATA_DIR, "reply_schema.json"))

class LicompToolkitSchemaChecker:

    def __init__(self):
        with open(SCHEMA_FILE) as fp:
            self.expr_expr_schema = json.load(fp)

    def __validate_deeply(self, compat):
        validations = 0
        lt = LicompToolkit()

        compat_check = compat['compatibility_check']
        if compat_check == 'outbound-license -> inbound-license':
            compat_object = compat['compatibility_object']
            if not compat_object:
                details = compat['compatibility_details']
            else:
                details = compat_object['compatibility_details']
            compatibilities = details['compatibilities']
            for compatibility_object in compatibilities:
                logging.debug(f'  {compatibility_object["resource_name"]}')
                inner_validations = lt.validate(compatibility_object)
                validations += 1
                logging.debug('Validation OK')
            return validations
        else:

            if compat_check == 'outbound-expression -> inbound-license' or compat_check == 'outbound-expression -> inbound-expression':
                compat_object = compat
            elif compat['compatibility_check'] == 'outbound-license -> inbound-expression':
                compat_object = compat['compatibility_object']
            else:
                raise LicompException("Validation failed. Invalid state: " + compat_check)

            for operand in compat_object['operands']:
                operand_compat_object = operand['compatibility_object']
                inner_validations = self.__validate_deeply(operand_compat_object)
                validations += inner_validations
            return validations

    def validate(self, content, deep=False):
        jsonschema.validate(instance=content,
                            schema=self.expr_expr_schema)
        validations = 1
        if deep:
            report = content['compatibility_report']
            validations = self.__validate_deeply(report)
        return validations

    def validate_file(self, filename, deep=False):
        with open(filename) as fp:
            return self.validate(json.load(fp), deep)
