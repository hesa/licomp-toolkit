#!/bin/env python3

# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys

from licomp.interface import LicompException

from licomp_toolkit.toolkit import LicompToolkit
from licomp_toolkit.toolkit import ExpressionExpressionChecker
from licomp_toolkit.format import LicompToolkitFormatter
from licomp_toolkit.config import cli_name
from licomp_toolkit.config import description
from licomp_toolkit.config import epilog
from licomp_toolkit.schema_checker import LicompToolkitSchemaChecker

from licomp.main_base import LicompParser
from licomp.interface import UseCase
from licomp.interface import Provisioning
from licomp.return_codes import ReturnCodes
from licomp.return_codes import compatibility_status_to_returncode

from flame.license_db import FossLicenses
from flame.exception import FlameException

class LicompToolkitParser(LicompParser):

    def __init__(self, name, description, epilog, default_usecase, default_provisioning):
        self.licomp_toolkit = LicompToolkit()
        LicompParser.__init__(self, self.licomp_toolkit, name, description, epilog, default_usecase, default_provisioning)
        self.flame = FossLicenses()

    def __normalize_license(self, lic_name):
        return self.flame.expression_license(lic_name, update_dual=False)['identified_license']

    def validate(self, args):
        LicompToolkitSchemaChecker().validate_file(args.file_name, deep=False)
        return "OK", ReturnCodes.LICOMP_OK.value, None

    def verify(self, args):
        formatter = LicompToolkitFormatter.formatter(self.args.output_format)
        try:
            expr_checker = ExpressionExpressionChecker()
            compatibilities = expr_checker.check_compatibility(self.__normalize_license(args.out_license),
                                                               self.__normalize_license(args.in_license),
                                                               args.usecase,
                                                               args.provisioning,
                                                               detailed_report=True)

            ret_code = compatibility_status_to_returncode(compatibilities['compatibility'])
            return formatter.format_compatibilities(compatibilities), ret_code, False
        except LicompException as e:
            return e, e.return_code.value, True
        except FlameException as e:
            return f'Illegal or missing license(s) supplied. Original message: {e}', ReturnCodes.LICOMP_ILLEGAL_LICENSE.value, True

    def supported_licenses(self, args):
        licenses = self.licomp_toolkit.supported_licenses()
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_resources(licenses), ReturnCodes.LICOMP_OK.value, None

    def supported_usecases(self, args):
        usecases = self.licomp_toolkit.supported_usecases()
        usecase_names = [UseCase.usecase_to_string(x) for x in usecases]
        return usecase_names, ReturnCodes.LICOMP_OK.value, None

    def supported_provisionings(self, args):
        provisionings = self.licomp_toolkit.supported_provisionings()
        provisioning_names = [Provisioning.provisioning_to_string(x) for x in provisionings]
        provisioning_names = list(provisioning_names)
        provisioning_names.sort()
        return provisioning_names, ReturnCodes.LICOMP_OK.value, None

    def supported_resources(self, args):
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_resources([f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values()]), ReturnCodes.LICOMP_OK.value, False

    def supports_license(self, args):
        lic = args.license
        licomp_resources = [f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values() if lic in x.supported_licenses()]
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_resources(licomp_resources), ReturnCodes.LICOMP_OK.value, None

    def supports_usecase(self, args):
        try:
            usecase = UseCase.string_to_usecase(args.usecase)
            licomp_resources = [f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values() if usecase in x.supported_usecases()]
            formatter = LicompToolkitFormatter.formatter(args.output_format)
            return formatter.format_licomp_resources(licomp_resources), ReturnCodes.LICOMP_OK.value, None
        except KeyError:
            return None, f'Use case "{args.usecase}" not supported. Supported use cases: {self.supported_usecases(args)[0]}'

    def supports_provisioning(self, args):
        try:
            provisioning = Provisioning.string_to_provisioning(args.provisioning)
            licomp_resources = [f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values() if provisioning in x.supported_provisionings()]
            formatter = LicompToolkitFormatter.formatter(args.output_format)
            return formatter.format_licomp_resources(licomp_resources), ReturnCodes.LICOMP_OK.value, None
        except KeyError:
            return None, f'Provisioning "{args.provisioning}" not supported. Supported provisionings: {self.supported_provisionings(args)[0]}'

    def versions(self, args):
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_versions(self.licomp_toolkit.versions()), ReturnCodes.LICOMP_OK.value, False

def _working_return_code(return_code):
    return return_code < ReturnCodes.LICOMP_LAST_SUCCESSFUL_CODE.value

def main():
    logging.debug("Licomp Toolkit")

    lct_parser = LicompToolkitParser(cli_name,
                                     description,
                                     epilog,
                                     UseCase.LIBRARY,
                                     Provisioning.BIN_DIST)

    subparsers = lct_parser.sub_parsers()

    # Command: list supported
    parser_sr = subparsers.add_parser('supported-resources', help='List all supported Licomp resources')
    parser_sr.set_defaults(which="supported_resources", func=lct_parser.supported_resources)

    parser_sl = subparsers.add_parser('supports-license', help='List the Licomp resources supporting the license')
    parser_sl.set_defaults(which="supports_license", func=lct_parser.supports_license)
    parser_sl.add_argument("license")

    parser_su = subparsers.add_parser('supports-usecase', help='List the Licomp resources supporting the usecase')
    parser_su.set_defaults(which="supports_usecase", func=lct_parser.supports_usecase)
    parser_su.add_argument("usecase")

    parser_sp = subparsers.add_parser('supports-provisioning', help='List the Licomp resources supporting the provisioning')
    parser_sp.set_defaults(which="supports_provisioning", func=lct_parser.supports_provisioning)
    parser_sp.add_argument("provisioning")

    # Command: list versions (of all toolkit and licomp resources)
    parser_sr = subparsers.add_parser('versions', help='Output version of licomp-toolkit and all the licomp resources')
    parser_sr.set_defaults(which="versions", func=lct_parser.versions)

    res, code, err, func = lct_parser.run_noexit()
    if _working_return_code(code):
        print(res)
    else:
        print(res, file=sys.stderr)

    return code


if __name__ == '__main__':
    sys.exit(main())
