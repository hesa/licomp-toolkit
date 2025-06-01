# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from licomp_toolkit.expr_parser import LicenseExpressionParser
from licomp.interface import LicompException

parser = LicenseExpressionParser()

def _type(expr):
    return expr['compatibility_type']

def _is_expression(expr):
    return expr['compatibility_type'] == 'expression'

def _is_license(expr):
    return expr['compatibility_type'] == 'license'

def _license(expr):
    return expr['license']

def _operator(expr):
    return expr['operator']

def _operands(expr):
    return expr['operands']

def test_none():
    with pytest.raises(LicompException):
        expression = parser.parse_license_expression(None)
        
def test_empty():
    with pytest.raises(LicompException):
        expression = parser.parse_license_expression('')
    
def test_single():
    expression = parser.parse_license_expression('MIT')
    assert _is_license(expression)
    assert _license(expression) == 'MIT'
    
def test_single_with():
    expression = parser.parse_license_expression('GPL-3.0-only WITH GCC-exception-3.1')
    assert _is_license(expression)
    assert _license(expression) == 'GPL-3.0-only WITH GCC-exception-3.1'
    
def test_simple_or():
    expression = parser.parse_license_expression('MIT OR X11')
    operands = [x['license'] for x in _operands(expression)]
    operands.sort()
    assert operands == [ 'MIT', 'X11' ]
    assert _is_expression(expression)
    assert _operator(expression) == 'OR'
    
def test_simple_or_with():
    expression = parser.parse_license_expression('MIT OR GPL-3.0-only WITH GCC-exception-3.1')
    operands = [x['license'] for x in _operands(expression)]
    operands.sort()
    assert operands == [  'GPL-3.0-only WITH GCC-exception-3.1', 'MIT' ]
    assert _is_expression(expression)
    assert _operator(expression) == 'OR'
    
def test_simple_or_with2():
    expression = parser.parse_license_expression('GPL-3.0-only WITH GCC-exception-3.1 OR MIT')
    operands = [x['license'] for x in _operands(expression)]
    operands.sort()
    assert operands == [  'GPL-3.0-only WITH GCC-exception-3.1', 'MIT' ]
    assert _is_expression(expression)
    assert _operator(expression) == 'OR'
    
def test_simple_and():
    expression = parser.parse_license_expression('MIT AND X11')
    operands = [x['license'] for x in _operands(expression)]
    operands.sort()
    assert operands == [ 'MIT', 'X11' ]
    assert _is_expression(expression)
    assert _operator(expression) == 'AND'

def test_simple_and_with():
    expression = parser.parse_license_expression('MIT AND GPL-3.0-only WITH GCC-exception-3.1')
    operands = [x['license'] for x in _operands(expression)]
    operands.sort()
    assert operands == [ 'GPL-3.0-only WITH GCC-exception-3.1', 'MIT' ]
    assert _is_expression(expression)
    assert _operator(expression) == 'AND'

def test_many_ors():
    expression = parser.parse_license_expression('MIT OR X11 OR BSD-3-Clause OR ISC')
    operands = [x['license'] for x in _operands(expression)]
    operands.sort()
    assert operands == [ 'BSD-3-Clause', 'ISC', 'MIT', 'X11' ]
    assert _is_expression(expression)
    assert _operator(expression) == 'OR'
    
def test_many_ands():
    expression = parser.parse_license_expression('MIT AND X11 AND BSD-3-Clause AND ISC AND GPL-3.0-only WITH GCC-exception-3.1')
    operands = [x['license'] for x in _operands(expression)]
    operands.sort()
    assert operands == [ 'BSD-3-Clause', 'GPL-3.0-only WITH GCC-exception-3.1', 'ISC', 'MIT', 'X11' ]
    assert _is_expression(expression)
    assert _operator(expression) == 'AND'

def test_many_complex_expr():
    expression = parser.parse_license_expression('MIT AND X11 AND (BSD-3-Clause OR ( ISC OR GPL-3.0-only WITH GCC-exception-3.1) )')
    assert _operator(expression) == 'AND'
    operands = _operands(expression)
    assert _license(operands[0]) == 'MIT'
    assert _license(operands[1]) == 'X11'
    assert _operator(operands[2]) == 'OR'
    operands = _operands(operands[2])
    assert _license(operands[0]) == 'BSD-3-Clause'
    assert _operator(operands[1]) == 'OR'
    operands = _operands(operands[1])
    assert _license(operands[0]) == 'ISC'
    assert _license(operands[1]) == 'GPL-3.0-only WITH GCC-exception-3.1'
    
    

