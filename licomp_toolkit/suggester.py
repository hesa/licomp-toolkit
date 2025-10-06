# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import re
import traceback

from licomp_toolkit.toolkit import LicompToolkit
from licomp_toolkit.toolkit import ExpressionExpressionChecker
from licomp.interface import Provisioning
from licomp.interface import UseCase

from flame.license_db import FossLicenses

class OutboundSuggester:
    """
    OutboundSuggester suggests outbound candidate licenses from a
    license expression

    If you have a license expression like this "BSD-3-Clause AND MIT
    AND GPL-2.0-only", typically the result of your dependencies'
    licenses, and want to know which outbound license you can chose.

    """
    def __init__(self):
        self._compatibility_rankings = {}
        self.lt = LicompToolkit()
        self.le = ExpressionExpressionChecker()
        self.flame = FossLicenses()

    def compatibility_rankings(self, usecase, provisioning):
        """ Returns a dict with ranked licenses based on your usecase/provisioning, e.g.

          {
             'GPL3':  {'count': 2, 'valids': '1', 'index': 69},
             'MIT':   {'count': 108, 'valids': '1', 'index': 169}
          }

          count - how many other licenses the license is compatible with (primary sort)
          valids - how many valid resources provided a 'yes' answer (secondary sort)
          index - index for the licenses, the higher index the more compatible (with other licenses)
        """
        if usecase in self._compatibility_rankings:
            if provisioning in self._compatibility_rankings[usecase]:
                return self._compatibility_rankings[usecase][provisioning]
        else:
            self._compatibility_rankings[usecase] = {}

        #
        # identify compatiblities
        lic_map = {}
        # loop through every license (against themselves)
        for in_lic in self.lt.supported_licenses():
            for out_lic in self.lt.supported_licenses():
                # get compat
                ret = self.lt.outbound_inbound_compatibility(out_lic,
                                                             in_lic,
                                                             UseCase.string_to_usecase(usecase),
                                                             Provisioning.string_to_provisioning(provisioning))
                results = ret['summary']['results']
                valid_results = results['nr_valid']
                # only increase the 'count' if the answers from the resources are only 'yes'
                yes = results.get('yes', {'count': 0, 'percent': 0.0})
                inc = 0
                if yes['percent'] == 100:
                    inc = 1

                lic_map[in_lic] = {
                    'count': lic_map.get(in_lic, {'count': 0})['count'] + inc,
                    'valids': valid_results,
                }

        # decorate (to sort list)
        decorated = [(lic_map[lic]['count'], lic_map[lic]['valids'], i, lic) for i, lic in enumerate(lic_map)]
        # sort after count, valids (in tuple)
        decorated.sort()
        # undecorate
        ordered_lic = [lic for count, valids, i, lic in decorated]

        # create new dict - use license name as key
        ordered_lic_map = {}
        for i, lic in enumerate(ordered_lic):
            ordered_lic_map[lic] = lic_map[lic]
            ordered_lic_map[lic]['index'] = i

        # store foar later (re)use
        self._compatibility_rankings[usecase][provisioning] = ordered_lic_map

        return self._compatibility_rankings[usecase][provisioning]

    def licenses(self, license_expr):
        """Returns a list of licenses in a license expression.

        If you have a license expression like this:
        "(MIT OR Apache-2.0) AND MIT AND GPL-2.0-only WITH Classpath-exception-2.0"

        you get a list like this:
        ["MIT", "Apache-2.0", "GPL-2.0-only WITH Classpath-exception-2.0"]

        """
        normalized = self.flame.expression_license(license_expr, update_dual=False)['identified_license']

        with_fixed = normalized.replace(' WITH ', '-WITH-')

        splits = [x.replace('-WITH-', ' WITH ') for x in re.split(r' AND | OR |\(|\)', with_fixed) if len(x) > 1]

        return splits

    def compat_licenses(self, license_expr, usecase, provisioning, licenses_to_check=None, resources=None):
        """Returns a list of licenses that are compatible with a license expression

        If you have a license expression like this:
        "(MIT OR Apache-2.0) AND MIT AND GPL-2.0-only"

        you get a list like this of licenses that are compatible with
        the expression listed in order of ranked compatibility. If you
        don't provide any licenses to check the functions defaults to
        looking at the licenses in the expressions itself. This you will get a list like this:

        ["GPL-2.0-only"]

        """
        compats = []
        if not licenses_to_check:
            licenses_to_check = self.licenses(license_expr)

        license_expression_parsed = self.flame.expression_license(license_expr, update_dual=False)['identified_license']
        for lic in licenses_to_check:
            logging.debug(f' check licenses: {lic}')
            try:
                ret = self.le.check_compatibility(lic,
                                                  license_expression_parsed,
                                                  usecase,
                                                  provisioning,
                                                  resources)
            except Exception as e:
                logging.debug(f'Exception caught: {e}')
                logging.debug(traceback.format_exc())
            if ret['compatibility'] == 'yes':
                compats.append(lic)
                logging.debug(f' appending: {lic}')

        # decorate compat list with indices (from rankings)
        decorated = [(self.__compat_index(lic, usecase, provisioning), lic) for lic in compats]

        # sort and reverse (to get the most compatible first)
        decorated.sort()
        decorated.reverse()

        # undecorate
        sorted_compats = [lic for index, lic in decorated]

        return sorted_compats

    def __compat_index(self, lic, usecase, provisioning):
        # returns the ranking index for a license,
        # given usecase and provisioning

        # initialize the ranking
        self.compatibility_rankings(usecase, provisioning)
        return self._compatibility_rankings[usecase][provisioning][lic]['index']
