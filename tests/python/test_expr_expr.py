# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import pytest
import logging
import sys

from licomp.interface import Licomp
from licomp.interface import Provisioning
from licomp.interface import UseCase
from licomp.interface import CompatibilityStatus

from licomp_toolkit.lic_expr import ExpressionExpressionChecker


eec = ExpressionExpressionChecker()

def _compat_status(report):
    return report['compatibility_report']['compatibility']

def _compat_type(report):
    return report['compatibility_report']['compatibility_type']

#
# license compat with license
#

# GPL-2.0-only -> MIT are compatible
def test_lic_lic_compat():
    compat_report = eec.check_compatibility('GPL-2.0-only', 'MIT',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'license'
    
# MIT -> GPL-2.0-only -> are NOT compatible
def test_lic_lic_incompat():
    compat_report = eec.check_compatibility('MIT', 'GPL-2.0-only',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'license'
    
#
# license compat with expression
#

# GPL-2.0-only -> MIT OR Apache-2.0 are compatible
def test_lic_expr_compat():
    compat_report = eec.check_compatibility('GPL-2.0-only', 'MIT OR Apache-2.0',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'license'

# GPL-2.0-only -> MIT AND Apache-2.0 are NOT compatible
def test_lic_expr_incompat():
    compat_report = eec.check_compatibility('GPL-2.0-only', 'MIT AND Apache-2.0',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'license'
        
#
# expression compat with license
#
# GPL-2.0-only AND BSD-3-Clause -> MIT are compatible
def test_expr_lic_compat():
    compat_report = eec.check_compatibility('GPL-2.0-only AND BSD-3-Clause', 'MIT',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'operator'

# GPL-2.0-only AND BSD-3-Clause -> Apache-2.0 are NOT compatible
def test_expr_lic_incompat():
    compat_report = eec.check_compatibility('GPL-2.0-only AND BSD-3-Clause', 'Apache-2.0',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'operator'
    
#
# expression compat with expression
#

# GPL-2.0-only AND BSD-3-Clause -> MIT AND X11 are compatible
def test_expr_expr_compat():
    compat_report = eec.check_compatibility('GPL-2.0-only AND BSD-3-Clause', 'MIT AND X11',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'operator'

# GPL-2.0-only AND BSD-3-Clause -> Apache-2.0 AND ISC are NOT compatible
def test_expr_expr_incompat():
    compat_report = eec.check_compatibility('GPL-2.0-only AND BSD-3-Clause', 'Apache-2.0 AND ISC',
                                            usecase=UseCase.LIBRARY,
                                           provisioning=Provisioning.BIN_DIST)
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'operator'

    
    
