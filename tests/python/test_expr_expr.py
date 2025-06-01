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

from licomp_toolkit.toolkit import ExpressionExpressionChecker

eec = ExpressionExpressionChecker()

GPLv2 = 'GPL-2.0-only'
MIT = 'MIT'
MIT_A_0BSD = 'MIT AND 0BSD'
APACHE2 = 'Apache-2.0'
APACHE2_A_ISC = 'Apache-2.0 AND ISC'
MIT_O_APACHE2 = 'MIT OR Apache-2.0'
MIT_A_APACHE2 = 'MIT AND Apache-2.0'
GPLv2_A_BSD3 = 'GPL-2.0-only AND BSD-3-Clause'


def _compat_status(report):
    return report['compatibility_report']['compatibility']

def _compat_type(report):
    return report['compatibility_report']['compatibility_type']

#
# license compat with license
#

# GPL-2.0-only -> MIT are compatible
def test_lic_lic_compat():
    compat_report = eec.check_compatibility(GPLv2, MIT,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'license'
    
# MIT -> GPL-2.0-only -> are NOT compatible
def test_lic_lic_incompat():
    compat_report = eec.check_compatibility(MIT, GPLv2,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'license'
    
#
# license compat with expression
#

# GPL-2.0-only -> MIT OR Apache-2.0 are compatible
def test_lic_expr_compat():
    compat_report = eec.check_compatibility(GPLv2, MIT_O_APACHE2,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'license'

# GPL-2.0-only -> MIT AND Apache-2.0 are NOT compatible
def test_lic_expr_incompat():
    compat_report = eec.check_compatibility(GPLv2, MIT_A_APACHE2,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'license'
        
#
# expression compat with license
#
# GPL-2.0-only AND BSD-3-Clause -> MIT are compatible
def test_expr_lic_compat():
    compat_report = eec.check_compatibility(GPLv2_A_BSD3, MIT,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'expression'

# GPL-2.0-only AND BSD-3-Clause -> Apache-2.0 are NOT compatible
def test_expr_lic_incompat():
    compat_report = eec.check_compatibility(GPLv2_A_BSD3, APACHE2,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'expression'
    
#
# expression compat with expression
#

# GPL-2.0-only AND BSD-3-Clause -> MIT AND 0BSD are compatible
def test_expr_expr_compat():
    compat_report = eec.check_compatibility(GPLv2_A_BSD3, MIT_A_0BSD,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'expression'

# GPL-2.0-only AND BSD-3-Clause -> Apache-2.0 AND ISC are NOT compatible
def test_expr_expr_incompat():
    compat_report = eec.check_compatibility(GPLv2_A_BSD3, APACHE2_A_ISC,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'expression'

    
    
OUTBOUND = f' ({GPLv2_A_BSD3} AND {GPLv2_A_BSD3} AND ({GPLv2_A_BSD3} AND ({GPLv2_A_BSD3} AND ({GPLv2_A_BSD3} AND {GPLv2_A_BSD3} ))) )'
    
INBOUND = f' ( {MIT_A_0BSD} AND {MIT_A_0BSD} AND {MIT_A_0BSD} AND {MIT_A_0BSD} ) '
INBOUND += f' AND ( {MIT_O_APACHE2} OR {MIT_O_APACHE2} OR {MIT_O_APACHE2} OR ( {MIT_O_APACHE2} OR {MIT_O_APACHE2} OR ( {MIT_O_APACHE2} AND {MIT_O_APACHE2} )) )'

def test_expr_expr_large_compat():
    
    compat_report = eec.check_compatibility(OUTBOUND,
                                            INBOUND,
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'yes'
    assert _compat_type(compat_report) == 'expression'

    
def test_expr_expr_large_incompat():
    
    compat_report = eec.check_compatibility(OUTBOUND,
                                            f'{INBOUND} AND {APACHE2}',
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'expression'

    
    
def test_expr_expr_with_1():

    # OSADL supports GPL-2.0-only WITH Classpath-exception-2.0
    # - usecase is SNIPPET
    compat_report = eec.check_compatibility(OUTBOUND,
                                            f'{INBOUND} AND GPL-2.0-only WITH Classpath-exception-2.0',
                                            usecase=UseCase.usecase_to_string(UseCase.SNIPPET),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))

    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'expression'

    
def test_expr_expr_with_2():
    
    compat_report = eec.check_compatibility(OUTBOUND,
                                            f'{INBOUND} AND GPL-2.0-only WITH Classpath-exception-2.0 AND {APACHE2}',
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    assert _compat_status(compat_report) == 'no'
    assert _compat_type(compat_report) == 'expression'

    
    
