#!/bin/env python3

# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from licomp_toolkit.toolkit import LicompToolkit
from licomp_toolkit.toolkit import LicompToolkitFormatter

from licomp.main_base import LicompParser
from licomp.interface import UseCase
from licomp.interface import Provisioning
from flame.license_db import FossLicenses

class LicompToolkitParser(LicompParser):

    def __init__(self, name, description, epilog, default_usecase, default_provisioning):
        LicompParser.__init__(self, None, name, description, epilog, default_usecase, default_provisioning)
        self.licomp_toolkit = LicompToolkit()
        self.flame = FossLicenses()

    def __normalize_license(self, lic_name):
        return self.flame.expression_license(lic_name, update_dual=False)['identified_license']

    def verify(self, args):
        compatibilities = self.licomp_toolkit.outbound_inbound_compatibility(self.__normalize_license(args.in_license),
                                                                             self.__normalize_license(args.out_license),
                                                                             args.usecase,
                                                                             args.provisioning)
        formatter = LicompToolkitFormatter.formatter(self.args.output_format)
        return formatter.format_compatibilities(compatibilities), False

    def supported_licenses(self, args):
        licenses = self.licomp_toolkit.supported_licenses()
        return licenses, None

    def supported_provisionings(self, args):
        provisionings = self.licomp_toolkit.supported_provisionings()
        provisioning_names = [Provisioning.provisioning_to_string(x) for x in provisionings]
        provisioning_names = list(provisioning_names)
        provisioning_names.sort()
        return provisioning_names, None

    def supported_resources(self, args):
        return [f"{x.name()}:{x.version()}" for x in self.licomp_modules.values()], False


def main():
    logging.debug("main")

    lct_parser = LicompToolkitParser('cli_name',
                                     'description',
                                     'epilog',
                                     UseCase.LIBRARY,
                                     Provisioning.BIN_DIST)

    subparsers = lct_parser.sub_parsers()
    parser_sr = subparsers.add_parser('supported-resources', help='slsl')
    parser_sr.set_defaults(which="supported_resources", func=lct_parser.supported_resources)

    lct_parser.run()


if __name__ == '__main__':
    main()
