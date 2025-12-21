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
from licomp_toolkit.suggester import OutboundSuggester
from licomp_toolkit.display_compatibility import DisplayCompatibility

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
        LicompToolkitSchemaChecker().validate_file(args.file_name, deep=True)
        return None, ReturnCodes.LICOMP_OK.value, None

    def _resources_to_use(self, args):
        lt = LicompToolkit()
        resources = args.resources
        new_resources = []
        unsupported = []
        if args.resources == ['all']:
            new_resources = list(lt.licomp_resources().keys())
            return new_resources, []
        for resource in resources:
            if 'licomp' not in resource:
                resource = f'licomp_{resource}'
            else:
                resource = resource.replace('-', '_')

            if not self.resource_avilable(resource):
                unsupported.append(resource)
            else:
                new_resources.append(resource)
        return new_resources, unsupported

    def verify(self, args):
        formatter = LicompToolkitFormatter.formatter(self.args.output_format)
        try:
            if args.no_verbose:
                detailed_report = False
            else:
                detailed_report = True

            resources, unsupported = self._resources_to_use(args)
            if unsupported:
                return f'Resource(s) {", ".join(unsupported)} is/are not supported', ReturnCodes.LICOMP_UNSUPPORTED_RESOURCE.value, True
            expr_checker = ExpressionExpressionChecker()
            compatibilities = expr_checker.check_compatibility(self.__normalize_license(args.out_license),
                                                               self.__normalize_license(args.in_license),
                                                               args.usecase,
                                                               args.provisioning,
                                                               resources=resources,
                                                               detailed_report=detailed_report)

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

    def simplify(self, args):
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        normalized = self.__normalize_license(' ' .join(args.license))
        simplified = self.licomp_toolkit.simplify(normalized)
        return formatter.format_licomp_licenses(simplified), ReturnCodes.LICOMP_OK.value, None

    def supported_resources(self, args):
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_resources(self.licomp_toolkit.licomp_resources_long()), ReturnCodes.LICOMP_OK.value, False

    def _supports_helper(self, key, value, output_format):
        licomp_resources = [x for x in self.licomp_toolkit.licomp_resources_long() if value in x[key]]
        formatter = LicompToolkitFormatter.formatter(output_format)
        return formatter.format_licomp_resources(licomp_resources)
    
    def supports_license(self, args):
        try:
            return self._supports_helper('licenses', args.license, args.output_format), ReturnCodes.LICOMP_OK.value, None
        except KeyError:
            return None, ReturnCodes.LICOMP_UNSUPPORTED_LICENSE.value, f'License "{args.license}" not supported.'

    def supports_usecase(self, args):
        try:
            return self._supports_helper('usecases', args.usecase, args.output_format), ReturnCodes.LICOMP_OK.value, None
        except KeyError:
            return None, ReturnCodes.LICOMP_UNSUPPORTED_USECASE.value, f'Use case "{args.usecase}" not supported. Supported use cases: {self.supported_usecases(args)[0]}'

    def supports_provisioning(self, args):
        try:
            return self._supports_helper('provisionings', args.provisioning, args.output_format), ReturnCodes.LICOMP_OK.value, None
        except KeyError:
            return None, ReturnCodes.LICOMP_UNSUPPORTED_PROVISIONING.value, f'Provisioning "{args.provisioning}" not supported. Supported provisionings: {self.supported_provisionings(args)[0]}'

    def outbound_candidate(self, args):
        suggester = OutboundSuggester()
        licenses_to_check = None
        if args.all_licenses:
            licenses_to_check = self.licomp_toolkit.supported_licenses()

        candidates = suggester.compat_licenses(args.license_expression,
                                               args.usecase,
                                               args.provisioning,
                                               licenses_to_check,
                                               args.resources)
        if args.least_compatible:
            candidates.reverse()

        formatter = LicompToolkitFormatter.formatter(args.output_format)

        return formatter.format_licomp_licenses(candidates), ReturnCodes.LICOMP_OK.value, None

    def display_compatibility(self, args):
        display_compat = DisplayCompatibility(self.licomp_toolkit)
        compats = display_compat.display_compatibility(args.licenses,
                                                       UseCase.string_to_usecase(args.usecase),
                                                       Provisioning.string_to_provisioning(args.provisioning),
                                                       args.resources)
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        formatted = formatter.format_display_compatibilities(compats,
                                                             {'discard_unsupported': args.discard_unsupported_licenses})
        return formatted, ReturnCodes.LICOMP_OK.value, None

    def versions(self, args):
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_versions(self.licomp_toolkit.versions()), ReturnCodes.LICOMP_OK.value, False

    def resource_avilable(self, resource):
        return resource in self.licomp_toolkit.licomp_resources().keys()

def _working_return_code(return_code):
    return return_code >= 0 and return_code < ReturnCodes.LICOMP_LAST_SUCCESSFUL_CODE.value

def main():
    logging.debug("Licomp Toolkit")

    lct_parser = LicompToolkitParser(cli_name,
                                     description,
                                     epilog,
                                     UseCase.LIBRARY,
                                     Provisioning.BIN_DIST)

    parser = lct_parser.parser
    subparsers = lct_parser.sub_parsers()

    parser.add_argument('-r', '--resources',
                        type=str,
                        action='append',
                        help='use specified licomp resource. For a list use the commands \'supported-resources\'. Use \'all\' to use all',
                        default=[])

    parser.add_argument('-nv', '--no-verbose',
                        action='store_true',
                        help='keep compatibility report as short as possible',
                        default=[])

    # Commands
    parser_si = subparsers.add_parser('simplify', help='Normalize and simplify a license expression')
    parser_si.set_defaults(which="simplify", func=lct_parser.simplify)
    parser_si.add_argument("license", type=str, nargs="+", help='License expression to simplify')

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

    parser_dc = subparsers.add_parser('display-compatibility', help='Display the compatibility between the supplied licenses')
    parser_dc.set_defaults(which="display_compatibility", func=lct_parser.display_compatibility)
    parser_dc.add_argument("licenses",
                           type=str,
                           nargs='+',
                           default=[])
    parser_dc.add_argument('-dul', '--discard-unsupported-licenses',
                           action='store_true',
                           help='Discard unsupported licenses from the output',
                           default=False)

    parser_ob = subparsers.add_parser('outbound-candidate', help='Identify outbound candidates to a license expression')
    parser_ob.set_defaults(which='outbound_candidate', func=lct_parser.outbound_candidate)
    parser_ob.add_argument("license_expression")
    parser_ob.add_argument('-al', '--all-licenses',
                           action='store_true',
                           help='Use all known licenses to identify outbound candidates',
                           default=False)
    parser_ob.add_argument('-lc', '--least-compatible',
                           action='store_true',
                           help='Sort the license according to least compatibility (i.e. from restrictive to permissive. Default is to list permissive to restrictive.',
                           default=False)

    # Command: list versions (of all toolkit and licomp resources)
    parser_sr = subparsers.add_parser('versions', help='Output version of licomp-toolkit and all the licomp resources')
    parser_sr.set_defaults(which="versions", func=lct_parser.versions)

    res, code, err, func = lct_parser.run_noexit()
    if _working_return_code(code):
        if res:
            print(res)
        else:
            print(err, file=sys.stderr)
    else:
        print(res, file=sys.stderr)

    return code


if __name__ == '__main__':
    sys.exit(main())
