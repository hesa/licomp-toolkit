# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import logging

from licomp.interface import Licomp
from licomp.interface import Provisioning
from licomp.interface import UseCase
from licomp.interface import CompatibilityStatus

from licomp_toolkit.toolkit import LicompToolkit

lt = LicompToolkit()

def test_supported():
    assert len(lt.supported_licenses()) > 60
    
def test_license_is_supported():
    assert lt.license_supported("BSD-3-Clause")
    
def test_license_is_not_supported():
    assert not lt.license_supported("Some-license-that-does-not-exist")
    
def test_provisioning_is_supported():
    assert lt.provisioning_supported(provisioning=Provisioning.BIN_DIST)
    
def test_provisioning_is_not_supported():
    assert not lt.provisioning_supported(provisioning=Provisioning.WEBUI)
    
def test_compat():
    ret = lt.outbound_inbound_compatibility("GPL-2.0-only", "BSD-3-Clause", UseCase.usecase_to_string(UseCase.LIBRARY), Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    logging.debug("ret: " + str(ret['summary']['results']))
    assert ret['summary']['results']['yes']['count'] == 3

def test_incompat():
    ret = lt.outbound_inbound_compatibility("BSD-3-Clause", "GPL-2.0-only",  UseCase.usecase_to_string(UseCase.LIBRARY), Provisioning.provisioning_to_string(Provisioning.BIN_DIST))
    logging.debug("ret: " + str(ret['summary']['results']))
    assert ret['summary']['results']['no']['count'] == 2

def test_incompat():
    ret = lt.outbound_inbound_compatibility("BSD-3-Clause", "GPL-2.0-only",  UseCase.usecase_to_string(UseCase.LIBRARY), Provisioning.provisioning_to_string(Provisioning.WEBUI))
    logging.debug("ret: " + str(ret['summary']['statuses']))
    # all five resources fail on webui
    assert len(ret['summary']['statuses']['failure']) == 6

def test_disclaimer():
    logging.debug(f'check disclaimer')
    assert lt.disclaimer()

