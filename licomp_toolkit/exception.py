# SPDX-FileCopyrightText: 2026 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

class LicompToolkitException(Exception):

    def __init__(self, message, error_code, orig_exception=None):
        self.message = message
        super().__init__(self.message)
        self.error_code = error_code
        self.original_exception = orig_exception
