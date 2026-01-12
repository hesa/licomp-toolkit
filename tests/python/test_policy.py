# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import pytest
import logging
import sys

from licomp_toolkit.license_policy import LicensePolicy
from licomp_toolkit.license_policy import DefaultLicensePolicy
from licomp_toolkit.license_policy import LicensePolicyHandler
from licomp_toolkit.toolkit import ExpressionExpressionChecker
from licomp.interface import UseCase
from licomp.interface import Provisioning

TEST_POLICY_FILE = 'tests/policy/license-policy.json'

policy = LicensePolicy(TEST_POLICY_FILE)
policy_handler = LicensePolicyHandler(TEST_POLICY_FILE)
expr_checker = ExpressionExpressionChecker()

def test_policy_allowed():
    assert "MIT" in policy.allowed()
    assert "BSD-3-Clause" in policy.allowed()

    assert "BSD-4-Clause" not in policy.allowed()
    assert "BSD-2-Clause-Patent" not in policy.allowed()
    
def test_policy_avoid():
    assert "MIT" not in policy.avoid()
    assert "BSD-3-Clause" not in policy.avoid()

    assert "BSD-4-Clause"  in policy.avoid()
    
    assert "BSD-2-Clause-Patent" not in policy.avoid()
    
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
    

# BRING BACK - RENAME
def _test_expr_expr_1(): 
    compat_report = _test_expr_expr_library_bin('MIT OR 0BSD', 'MIT OR (BSD-3-Clause AND MIT)')
    #compat_report = _test_expr_expr_library_bin('MIT', 'MIT')
    #print("cr: " + str(compat_report))
    policy_report = policy_handler.apply(compat_report)
    print("pr: " + str(policy_report))
    assert False


def test_default_policy():
    dpol = DefaultLicensePolicy(['licomp_reclicense'], 'library', 'binary-distribution')

    assert False
