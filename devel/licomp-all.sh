#!/bin/bash

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later



RESOURCES=$(./devel/licomp-toolkit supported-resources | jq -r .[] | cut -d : -f 1 | sed 's,_,-,g')

for RESOURCE in $RESOURCES
do
    echo "# $RESOURCE"
    $RESOURCE $*
done
