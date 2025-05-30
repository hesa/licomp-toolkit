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
from licomp_toolkit.schema_checker import LicompToolkitSchemaChecker

eec = ExpressionExpressionChecker()
checker = LicompToolkitSchemaChecker()

def test_lic_lic():
    compat_report = eec.check_compatibility("MIT", "BSD-3-Clause",
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST),
                                            detailed_report=True)
    
    ret = checker.validate(compat_report)
    print("Validating simple expression (non deep): " + str(ret))
    
    ret = checker.validate(compat_report, deep=True)
    print("Validating simple expression (deep): " + str(ret))

def test_lic_expr():
    compat_report = eec.check_compatibility("MIT", "BSD-3-Clause OR BSD-2-Clause",
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST),
                                            detailed_report=True)
    
    ret = checker.validate(compat_report)
    print("Validating license->expression (non deep): " + str(ret))
    
    ret = checker.validate(compat_report, deep=True)
    print("Validating license->expression (deep): " + str(ret))
    

def test_expr_lic():
    compat_report = eec.check_compatibility("MIT OR X11", "BSD-3-Clause",
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST),
                                            detailed_report=True)
    
    ret = checker.validate(compat_report)
    print("Validating expression->license (non deep): " + str(ret))
    
    ret = checker.validate(compat_report, deep=True)
    print("Validating expression->license (deep): " + str(ret))
    

def test_expr_expr():
    compat_report = eec.check_compatibility("MIT OR X11", "BSD-3-Clause OR BSD-2-Clause",
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST),
                                            detailed_report=True)
    
    ret = checker.validate(compat_report)
    print("Validating expression->expression (non deep): " + str(ret))
    
    ret = checker.validate(compat_report, deep=True)
    print("Validating expression->expression (deep): " + str(ret))
    
def test_expr_expr_many():
    compat_report = eec.check_compatibility("MIT OR X11 OR ISC AND MIT-0", "BSD-3-Clause OR BSD-2-Clause OR 0BSD AND Apache-2.0 AND 0BSD",
                                            usecase=UseCase.usecase_to_string(UseCase.LIBRARY),
                                            provisioning=Provisioning.provisioning_to_string(Provisioning.BIN_DIST),
                                            detailed_report=True)
    
    ret = checker.validate(compat_report)
    print("Validating expression->expression (non deep): " + str(ret))
    
    ret = checker.validate(compat_report, deep=True)
    print("Validating expression->expression (deep): " + str(ret))
    
