#!/bin/env python3

# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from licomp_toolkit.toolkit import LicompToolkit
from licomp_toolkit.toolkit import LicompToolkitFormatter
from licomp_toolkit.config import cli_name
from licomp_toolkit.config import description
from licomp_toolkit.config import epilog

from licomp.main_base import LicompParser
from licomp.interface import UseCase
from licomp.interface import Provisioning
from flame.license_db import FossLicenses

class LicompToolkitParser(LicompParser):

    def __init__(self, name, description, epilog, default_usecase, default_provisioning):
        self.licomp_toolkit = LicompToolkit()
        LicompParser.__init__(self, self.licomp_toolkit, name, description, epilog, default_usecase, default_provisioning)
        self.flame = FossLicenses()

    def __normalize_license(self, lic_name):
        return self.flame.expression_license(lic_name, update_dual=False)['identified_license']

    def verify(self, args):
        compatibilities = self.licomp_toolkit.outbound_inbound_compatibility(self.__normalize_license(args.out_license),
                                                                             self.__normalize_license(args.in_license),
                                                                             args.usecase,
                                                                             args.provisioning)
        formatter = LicompToolkitFormatter.formatter(self.args.output_format)
        return formatter.format_compatibilities(compatibilities), False

    def supported_licenses(self, args):
        licenses = self.licomp_toolkit.supported_licenses()
        return licenses, None

    def supported_usecases(self, args):
        usecases = self.licomp_toolkit.supported_usecases()
        usecase_names = [UseCase.usecase_to_string(x) for x in usecases]
        return usecase_names, None

    def supported_provisionings(self, args):
        provisionings = self.licomp_toolkit.supported_provisionings()
        provisioning_names = [Provisioning.provisioning_to_string(x) for x in provisionings]
        provisioning_names = list(provisioning_names)
        provisioning_names.sort()
        return provisioning_names, None

    def supported_resources(self, args):
        return [f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values()], False

    def supports_license(self, args):
        lic = args.license
        licomp_resources = [f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values() if lic in x.supported_licenses()]
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_resources(licomp_resources), None

    def supports_usecase(self, args):
        usecase = UseCase.string_to_usecase(args.usecase)
        licomp_resources = [f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values() if usecase in x.supported_usecases()]
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_resources(licomp_resources), None

    def supports_provisioning(self, args):
        provisioning = Provisioning.string_to_provisioning(args.provisioning)
        licomp_resources = [f'{x.name()}:{x.version()}' for x in self.licomp_toolkit.licomp_resources().values() if provisioning in x.supported_provisionings()]
        formatter = LicompToolkitFormatter.formatter(args.output_format)
        return formatter.format_licomp_resources(licomp_resources), None

    def versions(self, args):
        return self.licomp_toolkit.versions(), False

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

    parser_sl = subparsers.add_parser('supports-license', help='List the Licom resources supporting the license')
    parser_sl.set_defaults(which="supports_license", func=lct_parser.supports_license)
    parser_sl.add_argument("license")

    parser_su = subparsers.add_parser('supports-usecase', help='List the Licom resources supporting the usecase')
    parser_su.set_defaults(which="supports_usecase", func=lct_parser.supports_usecase)
    parser_su.add_argument("usecase")

    parser_sp = subparsers.add_parser('supports-provisioning', help='List the Licom resources supporting the provisioning')
    parser_sp.set_defaults(which="supports_provisioning", func=lct_parser.supports_provisioning)
    parser_sp.add_argument("provisioning")

    # Command: list versions (of all toolkit and licomp resources)
    parser_sr = subparsers.add_parser('versions', help='Output version of licomp-toolkit and all the licomp resources')
    parser_sr.set_defaults(which="versions", func=lct_parser.versions)

    lct_parser.run()


if __name__ == '__main__':
    main()
