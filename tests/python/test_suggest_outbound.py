# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

#
# Tests of OutboundSuggester 
#

from licomp_toolkit.suggester import OutboundSuggester

usecase = 'library'
provisioning = 'binary-distribution'
suggester = OutboundSuggester()


def test_compat_permissives():

    license_list = suggester.compat_licenses("(MIT AND ISC OR BSD-3-Clause AND Unlicense)", "library", "binary-distribution")
    assert 'MIT' in license_list
    assert 'ISC' in license_list
    assert 'BSD-3-Clause' in license_list
    assert 'Unlicense' in license_list
    
    assert license_list[0] == 'MIT' 

def test_compat_mixed_list():
    license_list = suggester.compat_licenses("(MIT AND GPL-2.0-or-later)", "library", "binary-distribution")
    assert 'GPL-2.0-or-later' in license_list
    assert 'GPL-3.0-or-later' not in license_list
    assert 'AGPL-3.0-or-later' not in license_list

def test_compat_mixed_list():
    license_list = suggester.compat_licenses("(MIT AND GPL-2.0-or-later)", "library", "binary-distribution", ["GPL-3.0-only", "GPL-2.0-only", "GPL-2.0-or-later", "AGPL-3.0-or-later"])
    assert 'GPL-2.0-or-later' in license_list
    assert 'GPL-3.0-only' in license_list
    assert 'AGPL-3.0-or-later' in license_list

def _ranked_index(ranked, lic):
    return ranked[lic]['index']
    
def test_ranked():
    ranked = suggester.compatibility_rankings(usecase, provisioning)
    # make sure the ranked index is higher the more permissive the license
    assert _ranked_index(ranked, "BSD-3-Clause") > _ranked_index(ranked, "LGPL-2.1-or-later") 
    assert _ranked_index(ranked, "BSD-3-Clause") > _ranked_index(ranked, "GPL-2.0-or-later") 
    assert _ranked_index(ranked, "BSD-3-Clause") == _ranked_index(ranked, "BSD-3-Clause") 
    assert _ranked_index(ranked, "LGPL-2.1-or-later") > _ranked_index(ranked, "GPL-2.0-or-later") 
