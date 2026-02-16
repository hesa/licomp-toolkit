# SPDX-FileCopyrightText: 2026 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

from licomp.return_codes import ReturnCodes

class LicompToolkitReturnCodes(Enum):
    LICOMP_TOOLKIT_INVALID_FILE = ReturnCodes.LICOMP_LAST_ERROR_CODE.value + 1

    LICOMP_TOOLKIT_LAST_ERROR_CODE = ReturnCodes.LICOMP_LAST_ERROR_CODE.value + 100
