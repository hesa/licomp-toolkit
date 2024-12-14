# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

#
# Test different resources against each other
#

import json
import pytest
import logging
import sys

from licomp.interface import Licomp
from licomp.interface import Provisioning
from licomp.interface import UseCase
from licomp.interface import CompatibilityStatus

from licomp_toolkit.toolkit import LicompToolkit

lt = LicompToolkit()

def _error(report):
    summary = report['summary']
    data = {
        'inbound': summary['inbound'],
        'outbound': summary['outbound'],
        'statuses': summary['compatibility_statuses']
    }
    print(str(data))
#    print(json.dumps(data, indent=4))
#    sys.exit(1)


def test_supported():
    licenses = lt.supported_licenses()

    usecase = UseCase.LIBRARY
    provisioning = Provisioning.BIN_DIST

    unsupported = 0
    supported = 0
    successes = 0
    failures = 0
    for in_lic in licenses:
        for out_lic in licenses:
            ret = lt.outbound_inbound_compatibility(out_lic,
                                                    in_lic,
                                                    UseCase.usecase_to_string(usecase),
                                                    Provisioning.provisioning_to_string(provisioning))
            results = ret['summary']['results']
            if int(results['nr_valid']) == 0:
                unsupported += 1
                continue
            else:
                supported += 1
                if 'yes' in results:
                    if not (results['yes']['percent'] == 100.00):
                        _error(ret)
                        failures += 1
                    else:
                        successes += 1
                elif 'no' in results:
                    if not (results['no']['percent'] == 100.00):
                        _error(ret)
                        failures += 1
                    else:
                        successes += 1
                elif 'unknown' in results:
                    if not (results['unknown']['percent'] == 100.00):
                        _error(ret)
                        failures += 1
                    else:
                        successes += 1
                else:
                    print(" woha...: " + str(results))
                    

            #print(str(results['percent']))

    nr_licenses = len(licenses)
    print("Licenses:     " + str(nr_licenses) + "  => " + str(nr_licenses * nr_licenses))
    print("Supported:    " + str(supported))
    print("Unsupported:  " + str(unsupported))
    print("Failures:     " + str(failures))
    print("Successes:    " + str(successes))
test_supported()
        
    
