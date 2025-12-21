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
resource_names = [x for x in lt.licomp_resources()]
standard_resource_names = [x for x in lt.licomp_standard_resources()]
optional_resource_names = [x for x in lt.licomp_optional_resources()]

def test_supported_resources():
    assert len(lt.licomp_resources()) == 6
    
def test_supported_resources():
    assert "licomp_reclicense" in resource_names
    assert "licomp_osadl" in resource_names
    assert "licomp_proprietary" in resource_names
    assert "licomp_hermione" in resource_names
    assert "licomp_dwheeler" in resource_names
    assert "licomp_gnuguide" in resource_names

def test_supported_resources_standard():
    assert "licomp_reclicense" in standard_resource_names
    assert "licomp_osadl" in standard_resource_names
    assert "licomp_proprietary" not in standard_resource_names
    assert "licomp_hermione" not in standard_resource_names
    assert "licomp_dwheeler" not in standard_resource_names
    assert "licomp_gnuguide" not in standard_resource_names

def test_supported_resources_standard():
    assert "licomp_reclicense" not in optional_resource_names
    assert "licomp_osadl" not in optional_resource_names
    assert "licomp_proprietary" in optional_resource_names
    assert "licomp_hermione" in optional_resource_names
    assert "licomp_dwheeler" in optional_resource_names
    assert "licomp_gnuguide" in optional_resource_names
