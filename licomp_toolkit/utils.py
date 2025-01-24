# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

from licomp.return_codes import compatibility_status_to_returncode
from licomp.return_codes import ReturnCodes

def licomp_results_to_return_code(licomp_results):
    nr_results = len(licomp_results) - 1 # -1 since 'nr_valid' included in the results

    if nr_results == 0:
        return ReturnCodes.LICOMP_UNSUPPORTED_LICENSE.value

    if nr_results != 1:
        return ReturnCodes.LICOMP_INCONSISTENCY.value

    # we only have on result (apart from 'nr_valid')
    for result in licomp_results:
        if result == 'nr_valid':
            continue
        return compatibility_status_to_returncode(result)

    return ReturnCodes.LICOMP_INTERNAL_ERROR.value
