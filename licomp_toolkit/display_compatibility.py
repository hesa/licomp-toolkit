# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

class DisplayCompatibility:

    def __init__(self, licomp_toolkit):
        self.licomp_toolkit = licomp_toolkit

    def display_compatibility(self, licenses, usecase, provisioning, resources):
        compats = {}
        for outbound in licenses:
            compats[outbound] = {}
            for inbound in licenses:
                ret = self.licomp_toolkit.outbound_inbound_compatibility(outbound,
                                                                         inbound,
                                                                         usecase,
                                                                         provisioning,
                                                                         resources)
                compats[outbound][inbound] = ret
        return compats
