# SPDX-FileCopyrightText: 2026 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import pytest
import logging
import sys

from licomp_toolkit.license_policy import LicensePolicy
from licomp_toolkit.license_policy import DefaultLicensePolicy
from licomp_toolkit.license_policy import LicensePolicyException
from licomp_toolkit.license_policy import LicensePolicyHandler
from licomp_toolkit.toolkit import ExpressionExpressionChecker
from licomp.interface import UseCase
from licomp.interface import Provisioning

TEST_POLICY_FILE = 'tests/policy/license-policy.json'

policy = LicensePolicy(TEST_POLICY_FILE)
policy_handler = LicensePolicyHandler(TEST_POLICY_FILE)
default_policy_handler = LicensePolicyHandler(
    resources = ['licomp_reclicense'],
    usecase = 'library',
    provisioning = 'binary-distribution')
expr_checker = ExpressionExpressionChecker()

default_policy = DefaultLicensePolicy(
    ['licomp_reclicense'],
    'library',
    'binary-distribution')
    

def test_policy_allowed():
    assert "MIT" in policy.allowed()
    assert "BSD-3-Clause" in policy.allowed()

    assert "BSD-4-Clause" not in policy.allowed()
    assert "BSD-2-Clause-Patent" not in policy.allowed()
    
def test_policy_avoided():
    assert "MIT" not in policy.avoided()
    assert "BSD-3-Clause" not in policy.avoided()

    assert "BSD-4-Clause"  in policy.avoided()
    
    assert "BSD-2-Clause-Patent" not in policy.avoided()
    
def test_policy_denied():
    assert "MIT" not in policy.denied()
    assert "BSD-3-Clause" not in policy.denied()

    assert "BSD-4-Clause"  not in policy.denied()
    
    assert "BSD-2-Clause-Patent" in policy.denied()

def test_meta():
    assert policy.meta() != None

def _test_expr_expr_library_bin(outbound, inbound, policy_file=None):
    compats = expr_checker.check_compatibility(outbound,
                                               inbound,
                                               'library',
                                               'binary-distribution')
    return compats
    

def test_policy_preferences_allowed():
    assert policy.compare_preferences('MIT', 'BSD-3-Clause') < 0
    assert policy.compare_preferences('BSD-3-Clause', 'MIT') > 0
    assert policy.compare_preferences('BSD-3-Clause', 'BSD-3-Clause') == 0
    
def test_policy_preferences_allowed_avoided():
    assert policy.compare_preferences('MIT', 'BSD-4-Clause') < 0
    assert policy.compare_preferences('BSD-4-Clause', 'MIT') > 0
    assert policy.compare_preferences('BSD-4-Clause', 'BSD-4-Clause') == 0
    
def test_policy_preferences_allowed_denied():
    assert policy.compare_preferences('BSD-3-Clause', 'BSD-3-Clause') == 0
    assert policy.compare_preferences('MIT', 'BSD-2-Clause-Patent') < 0
    assert policy.compare_preferences('BSD-2-Clause-Patent', 'MIT') > 0
    assert policy.compare_preferences('BSD-2-Clause-Patent', 'BSD-2-Clause-Patent') == None
    
def test_policy_preferences_allowed_denied_ignore():
    assert policy.compare_preferences('MIT', 'BSD-2-Clause-Patent', ignore_missing=True) < 0
    assert policy.compare_preferences('BSD-2-Clause-Patent', 'BSD-2-Clause-Patent', ignore_missing=True) == None

def test_policy_preferences_allowed_denied_names():
    assert policy.most_preferred('MIT', 'BSD-3-Clause') == 'MIT'
    assert policy.most_preferred('MIT', 'BSD-2-Clause-Patent') == 'MIT'
    assert policy.most_preferred('BSD-2-Clause-Patent', 'BSD-3-Clause') == 'BSD-3-Clause'
    assert policy.most_preferred('BSD-2-Clause-Patent', 'BSD-2-Clause-Patent') == None
    
def test_policy_preferences_allowed_denied_names_ignore():
    assert policy.most_preferred('BSD-2-Clause-Patent', 'BSD-3-Clause', ignore_missing=True) == 'BSD-3-Clause'
    assert policy.most_preferred('BSD-2-Clause-Patent', 'BSD-2-Clause-Patent', ignore_missing=True) == None

def OBSOLETE_test_policy_preferred_score_ignore_missing():
    assert policy.preferred_score_ignore_missing('MIT', 'BSD-3-Clause') == -1
    assert policy.preferred_score_ignore_missing('BSD-3-Clause', 'BSD-3-Clause') == 0
    assert policy.preferred_score_ignore_missing('BSD-3-Clause', 'MIT') == 1

def OBSOLETE_test_policy_sorted():
    assert policy.preferred_score_ignore_missing('MIT', 'BSD-3-Clause') == -1
    assert policy.preferred_score_ignore_missing('BSD-3-Clause', 'BSD-3-Clause') == 0
    assert policy.preferred_score_ignore_missing('BSD-3-Clause', 'MIT') == 1
    assert policy.preferred_score_ignore_missing('BSD-3-Clause', 'GPL-2.0-or-later') == -1
    from functools import cmp_to_key
    inbounds = ['MIT', 'GPL-2.0-or-later', 'BSD-3-Clause']
    sorted_inbounds = sorted(inbounds, key=cmp_to_key(policy.preferred_score_ignore_missing))
    print("TEST: " + str(inbounds))
    print("TEST: " + str(sorted_inbounds))
    assert sorted_inbounds == ['MIT', 'BSD-3-Clause', 'GPL-2.0-or-later']
    

def test_policy_preferences_raises():
    with pytest.raises(LicensePolicyException) as e_info:
        policy.most_preferred('MIT2', 'GPL-2.0-or-later2')
    with pytest.raises(LicensePolicyException) as e_info:
        policy.most_preferred('MIT2', 'GPL-2.0-or-later2', ignore_missing=False)

def test_policy_preferences_raises_ignore():
    policy.most_preferred('MIT2', 'GPL-2.0-or-later2', ignore_missing=True) == None

# BRING BACK - RENAME
def _test_expr_expr_1(): 
    compat_report = _test_expr_expr_library_bin('MIT OR 0BSD', 'MIT OR (BSD-3-Clause AND MIT)')
    #compat_report = _test_expr_expr_library_bin('MIT', 'MIT')
    #print("cr: " + str(compat_report))
    policy_report = policy_handler.apply(compat_report)
    print("pr: " + str(policy_report))
    assert False


def test_default_policy_listed():
    assert "MIT" in default_policy.allowed()
    assert "BSD-3-Clause" in default_policy.allowed()

    assert "BSD-4-Clause" in default_policy.allowed()
    assert "BSD-2-Clause-Patent" in default_policy.allowed()

    assert len(default_policy.avoided()) == 0
    assert len(default_policy.denied()) == 0

def test_default_policy_preference():
    assert default_policy.compare_preferences('MIT', 'GPL-2.0-or-later') < 0
    assert default_policy.compare_preferences('GPL-2.0-or-later', 'MIT') > 0
    assert default_policy.compare_preferences('MIT', 'MIT') == 0

def test_default_policy_preferences_allowed_denied_names():
    assert default_policy.most_preferred('BSD-3-Clause', 'BSD-3-Clause') == 'BSD-3-Clause'
    assert default_policy.most_preferred('MIT', 'BSD-3-Clause') == 'MIT'
    assert default_policy.most_preferred('MIT', 'GPL-2.0-or-later') == 'MIT'

    
def test_default_policy_preferences_raises():
    with pytest.raises(LicensePolicyException) as e_info:
        default_policy.most_preferred('MIT2', 'GPL-2.0-or-later2')
    
def test_preferred_score_inbounds():
    OBSD_MIT = {'outbound': {'license': 'MIT', 'type': 'license', 'preferences': {'license': 'MIT', 'license_list': 'allowed', 'license_index': 3}}, 'inbound': {'license': '0BSD', 'type': 'license', 'preferences': {'license': '0BSD', 'license_list': 'allowed', 'license_index': 2}}, 'compatibility': 'yes', 'unusable': {'unusable': []}}
    #{'check_type': 'inbound', 'inbound_license': '0BSD', 'outbound_license': 'MIT', 'inbound_license_type': 'license', 'outbound_license_type': 'license', 'compatibility': 'yes', 'inbound_list': 'allowed', 'inbound_list_index': 3}
    
    ISC_MIT = {'outbound': {'license': 'MIT', 'type': 'license', 'preferences': {'license': 'MIT', 'license_list': 'allowed', 'license_index': 3}}, 'inbound': {'license': 'ISC', 'type': 'license', 'preferences': {'license': 'ISC', 'license_list': 'allowed', 'license_index': 4}}, 'compatibility': 'yes', 'unusable': {'unusable': []}}
    #{'check_type': 'inbound', 'inbound_license': 'ISC', 'outbound_license': 'MIT', 'inbound_license_type': 'license', 'outbound_license_type': 'license', 'compatibility': 'yes', 'inbound_list': 'allowed', 'inbound_list_index': 7}

    assert default_policy.preferred_score_inbounds(OBSD_MIT, ISC_MIT) < 0
    assert default_policy.preferred_score_inbounds(ISC_MIT, OBSD_MIT) > 0
    assert default_policy.preferred_score_inbounds(ISC_MIT, ISC_MIT) == 0
        
def test_scored_inbounds_zerobsd_isc():
    inbounds =  [
        {
            "outbound": {
                "license": "MIT",
                "type": "license",
                "preferences": {
                    "license": "MIT",
                    "license_list": "allowed",
                    "license_index": 0
                }
            },
            "inbound": {
                "license": "0BSD",
                "type": "license",
                "preferences": {
                    "license": "0BSD",
                    "license_list": "allowed",
                    "license_index": 4
                }
            },
            "compatibility": "yes",
            "unusable": []
        },
        {
            "outbound": {
                "license": "MIT",
                "type": "license",
                "preferences": {
                    "license": "MIT",
                    "license_list": "allowed",
                    "license_index": 0
                }
            },
            "inbound": {
                "license": "ISC",
                "type": "license",
                "preferences": {
                    "license": "ISC",
                    "license_list": "",
                    "license_index": None
                }
            },
            "compatibility": "yes",
            "unusable": []
        }
    ]

    scored_inbounds, unusable = default_policy_handler.scored_inbounds(inbounds, "OR")
    assert len(scored_inbounds) == 2
    assert len(scored_inbounds[0]['inbound']) == 3
    assert scored_inbounds[0]['inbound']['license'] == '0BSD'
    assert scored_inbounds[1]['inbound']['license'] == 'ISC'

        
def test_scored_inbounds_isc_zerobsd():
    inbounds = [
        {
            "outbound": {
                "license": "MIT",
                "type": "license",
                "preferences": {
                    "license": "MIT",
                    "license_list": "allowed",
                    "license_index": 0
                }
            },
            "inbound": {
                "license": "ISC",
                "type": "license",
                "preferences": {
                    "license": "ISC",
                    "license_list": "",
                    "license_index": None
                }
            },
            "compatibility": "yes",
            "unusable": []
        },
        {
            "outbound": {
                "license": "MIT",
                "type": "license",
                "preferences": {
                    "license": "MIT",
                    "license_list": "allowed",
                    "license_index": 0
                }
            },
            "inbound": {
                "license": "0BSD",
                "type": "license",
                "preferences": {
                    "license": "0BSD",
                    "license_list": "allowed",
                    "license_index": 4
                }
            },
            "compatibility": "yes",
            "unusable": []
        }
    ]

    scored_inbounds, unusable = default_policy_handler.scored_inbounds(inbounds, "OR")
    assert len(scored_inbounds) == 2
    assert len(scored_inbounds[0]['inbound']) == 3
    assert scored_inbounds[0]['inbound']['license'] == '0BSD'
    assert scored_inbounds[1]['inbound']['license'] == 'ISC'

    
def test_usable_license():
    LIC = {'outbound': {'license': 'MIT', 'type': 'license', 'preferences': {'license': 'MIT', 'license_list': 'allowed', 'license_index': 3}}, 'inbound': {'license': 'BSD-3-Clause', 'type': 'license', 'preferences': {'license': 'BSD-3-Clause', 'license_list': 'allowed', 'license_index': 2}}, 'compatibility': 'no', 'unusable': {'unusable': []}}
    
    assert not policy_handler.usable_license(LIC, 'inbound')
    assert not policy_handler.usable_license(LIC, 'outbound')

    LIC['compatibility'] = 'yes'
    assert policy_handler.usable_license(LIC, 'inbound')
    assert policy_handler.usable_license(LIC, 'outbound')

