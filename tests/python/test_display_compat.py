# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

#
# Tests of DisplayCompatibility
#

from licomp_toolkit.toolkit import LicompToolkit
from licomp_toolkit.display_compatibility import DisplayCompatibility
from licomp_toolkit.format import LicompToolkitFormatter
from licomp.interface import UseCase
from licomp.interface import Provisioning

import json
import re

usecase = UseCase.LIBRARY
provisioning = Provisioning.BIN_DIST
licomp_toolkit = LicompToolkit()
display_compat = DisplayCompatibility(licomp_toolkit)
dot_formatter = LicompToolkitFormatter.formatter('dot')
json_formatter = LicompToolkitFormatter.formatter('json')


#
# json output
#
def test_json_display_mit_bsd3():
    licenses = ['MIT', 'BSD-3-Clause']
    resources = ['licomp_reclicense']

    compats = display_compat.display_compatibility(licenses,
                                                   usecase,
                                                   provisioning,
                                                   resources)
    formatted = json.loads(json_formatter.format_display_compatibilities(compats))
    
    assert formatted['MIT']['MIT'] == ['yes']
    assert formatted['MIT']['BSD-3-Clause'] == ['yes']
    assert formatted['BSD-3-Clause']['MIT'] == ['yes']
    assert formatted['BSD-3-Clause']['BSD-3-Clause'] == ['yes']


def test_json_display_apache_gpl2_reclicense():
    licenses = ['Apache-2.0', 'GPL-2.0-only']
    resources = ['licomp_reclicense']
    compats = display_compat.display_compatibility(licenses,
                                                   usecase,
                                                   provisioning,
                                                   resources)
    formatted = json.loads(json_formatter.format_display_compatibilities(compats))
    assert formatted['Apache-2.0']['Apache-2.0'] == ['yes']
    assert formatted['Apache-2.0']['GPL-2.0-only'] == ['no']
    assert formatted['GPL-2.0-only']['Apache-2.0'] == ['no']
    assert formatted['GPL-2.0-only']['GPL-2.0-only'] == ['yes']


def test_json_display_apache_gpl2_osadl():
    licenses = ['Apache-2.0', 'GPL-2.0-only']
    resources = ['licomp_osadl']
    compats = display_compat.display_compatibility(licenses,
                                                   UseCase.SNIPPET,
                                                   provisioning,
                                                   resources)
    formatted = json.loads(json_formatter.format_display_compatibilities(compats))
    assert formatted['Apache-2.0']['Apache-2.0'] == ['yes']
    assert formatted['Apache-2.0']['GPL-2.0-only'] == ['no']
    assert formatted['GPL-2.0-only']['Apache-2.0'] == ['no']
    assert formatted['GPL-2.0-only']['GPL-2.0-only'] == ['yes']


#
# dot output
#

def _build_expr(license1, license2, first_expr):
    return '"' + license1 + '"[ ]*->[ ]*"' + license2 + r'"[ ]*\[[ ]*' + str(first_expr)

def test_display_mit_bsd3():
    licenses = ['MIT', 'BSD-3-Clause']
    resources = ['licomp_reclicense']

    compats = display_compat.display_compatibility(licenses,
                                                   usecase,
                                                   provisioning,
                                                   resources)
    formatted = dot_formatter.format_display_compatibilities(compats)

    assert re.search(_build_expr('MIT', 'BSD-3-Clause', 'dir="both"'), formatted)

def test_display_apache_bsd3():
    licenses = ['Apache-2.0', 'BSD-3-Clause']
    resources = ['licomp_reclicense']

    compats = display_compat.display_compatibility(licenses,
                                                   usecase,
                                                   provisioning,
                                                   resources)
    formatted = dot_formatter.format_display_compatibilities(compats)

    assert re.search(_build_expr('Apache-2.0', 'BSD-3-Clause', 'dir="both"'), formatted)

def test_display_apache_gpl2_reclicense():
    licenses = ['Apache-2.0', 'GPL-2.0-only']
    resources = ['licomp_reclicense']
    compats = display_compat.display_compatibility(licenses,
                                                   usecase,
                                                   provisioning,
                                                   resources)
    formatted = dot_formatter.format_display_compatibilities(compats)
    assert re.search(_build_expr('Apache-2.0', 'GPL-2.0-only', 'dir="both" color="darkred"'), formatted)

def test_display_apache_gpl2_osadl():
    licenses = ['Apache-2.0', 'GPL-2.0-only']
    resources = ['licomp_osadl']
    compats = display_compat.display_compatibility(licenses,
                                                   UseCase.SNIPPET,
                                                   provisioning,
                                                   resources)
    formatted = dot_formatter.format_display_compatibilities(compats)
    assert re.search(_build_expr('Apache-2.0', 'GPL-2.0-only', 'dir="both"[ ]*color="darkred"'), formatted)

#
# test unsupported output
#
def test_display_apache_gpl2_osadl_unsupported_1():
    licenses = ['Apache-2.0', 'GPL-2.0-only', 'BSD-Santa-Clause']
    resources = ['licomp_osadl']
    compats = display_compat.display_compatibility(licenses,
                                                   UseCase.SNIPPET,
                                                   provisioning,
                                                   resources)
    formatted = dot_formatter.format_display_compatibilities(compats)
    # By default, unsupported should be part of the output
    assert re.search(_build_expr('Apache-2.0', 'BSD-Santa-Clause', 'dir="both"[ ]*color="yellow"'), formatted)
    assert re.search(_build_expr('GPL-2.0-only', 'BSD-Santa-Clause', 'dir="both"[ ]*color="yellow"'), formatted)

    # False: unsupported should be part of the output
    formatted = dot_formatter.format_display_compatibilities(compats, {'discard_unsupported': False})
    assert re.search(_build_expr('Apache-2.0', 'BSD-Santa-Clause', 'dir="both"[ ]*color="yellow"'), formatted)
    assert re.search(_build_expr('GPL-2.0-only', 'BSD-Santa-Clause', 'dir="both"[ ]*color="yellow"'), formatted)

    # True: unsupported should NOT be part of the output
    formatted = dot_formatter.format_display_compatibilities(compats, {'discard_unsupported': True})
    assert not 'BSD-Santa-Clause' in formatted

