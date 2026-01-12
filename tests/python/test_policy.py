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
expr_checker = ExpressionExpressionChecker()

default_policy = DefaultLicensePolicy(['licomp_reclicense'], 'library', 'binary-distribution')

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

def test_policy_preferences_raises():
    with pytest.raises(LicensePolicyException) as e_info:
        policy.most_preferred('MIT2', 'GPL-2.0-or-later2')

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
    assert default_policy.most_preferred('MIT', 'BSD-3-Clause') == 'MIT'
    assert default_policy.most_preferred('MIT', 'GPL-2.0-or-later') == 'MIT'

    
def test_default_policy_preferences_raises():
    with pytest.raises(LicensePolicyException) as e_info:
        default_policy.most_preferred('MIT2', 'GPL-2.0-or-later2')
    
