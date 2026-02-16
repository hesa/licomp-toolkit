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
    
def _test_expr_expr_library_bin(outbound, inbound):
    report = expr_checker.check_compatibility(outbound,
                                               inbound,
                                               'library',
                                               'binary-distribution')
    policy_report = policy_handler.apply_policy(report)
    policy_report_default = default_policy_handler.apply_policy(report)
    
    return report, policy_report, policy_report_default
    


def test_lic_lic():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT',
        'BSD-3-Clause'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == 'MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-3-Clause'
    
    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == 'MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-3-Clause'
    
    

def test_lic_expr_and():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT',
        'BSD-3-Clause AND 0BSD'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause AND 0BSD'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == 'MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == '0BSD AND BSD-3-Clause'
    
    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause AND 0BSD'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == 'MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == '0BSD AND BSD-3-Clause'
    
    
def test_lic_expr_or():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT',
        'BSD-3-Clause OR 0BSD'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause OR 0BSD'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == 'MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == '0BSD'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause OR 0BSD'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == 'MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == '0BSD'
    
    
def test_expr_lic_or():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT OR 0BSD',
        'BSD-3-Clause'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT OR 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT OR 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-3-Clause'
    
    
def test_expr_lic_and():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT AND 0BSD',
        'BSD-3-Clause'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-3-Clause'

    
def test_expr_expr_or():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT OR 0BSD',
        'BSD-2-Clause OR BSD-3-Clause'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT OR 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause OR BSD-3-Clause'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT OR 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause OR BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause'
    
    
def test_expr_expr_and():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT AND 0BSD',
        'BSD-2-Clause AND BSD-3-Clause'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND BSD-3-Clause'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause AND BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND BSD-3-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause AND BSD-3-Clause'

def test_expr_expr_incompat():
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT AND 0BSD',
        'BSD-2-Clause AND GPL-2.0-or-later'
    )
    
    assert report['compatibility_report']['compatibility'] == 'no'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND GPL-2.0-or-later'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == None
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == None

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND GPL-2.0-or-later'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == None
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == None

def test_expr_expr_bad_license_or():
    # X11 not supported by licomp_reclicense, but we have and OR so should be compatible
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT AND 0BSD',
        'BSD-2-Clause OR X11'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause OR X11'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause OR X11'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause'

def test_expr_expr_bad_license_and():
    # X11 not supported by licomp_reclicense
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT AND 0BSD',
        'BSD-2-Clause AND X11'
    )
    
    assert report['compatibility_report']['compatibility'] == 'no'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND X11'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == None
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == None

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND X11'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == None
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == None

def test_expr_expr_no_license_or():
    # MONKEYWRENCH is not a license
    # ... and nor supported by licomp_reclicense
    # ... and not in a policy list
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT AND 0BSD',
        'BSD-2-Clause OR MONKEYWRENCH'
    )
    
    assert report['compatibility_report']['compatibility'] == 'yes'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause OR MONKEYWRENCH'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause OR MONKEYWRENCH'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == '0BSD AND MIT'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == 'BSD-2-Clause'


def test_expr_expr_no_license_and():
    # MONKEYWRENCH is not a license
    # ... and nor supported by licomp_reclicense
    # ... and not in a policy list
    
    report, policy_report, policy_report_default = _test_expr_expr_library_bin(
        'MIT AND 0BSD',
        'BSD-2-Clause AND MONKEYWRENCH'
    )
    
    assert report['compatibility_report']['compatibility'] == 'no'

    assert policy_report['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND MONKEYWRENCH'

    assert policy_report['compatibility_report']['policy_check']['outbound']['preferences']['license'] == None
    assert policy_report['compatibility_report']['policy_check']['inbound']['preferences']['license'] == None

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['license'] == 'MIT AND 0BSD'
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['license'] == 'BSD-2-Clause AND MONKEYWRENCH'

    assert policy_report_default['compatibility_report']['policy_check']['outbound']['preferences']['license'] == None
    assert policy_report_default['compatibility_report']['policy_check']['inbound']['preferences']['license'] == None

#     with pytest.raises(LicensePolicyException):
