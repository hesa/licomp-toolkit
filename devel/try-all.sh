#!/bin/bash

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Loop over every supported license. Useful if you want to:
# * make sure there are no crashes
# * searching for return values

LICENSES=$(devel/licomp-toolkit --local supported-licenses | cut -d : -f2 | tr "," " " | sed "s,['\[],,g" | tr "]" " " )

for outlic in $LICENSES ;
do
    for inlic in $LICENSES;
    do
        CMD="./devel/licomp-toolkit --local verify -ol $outlic -il $inlic";
        echo $CMD;
        $CMD ;
    done;
done 2>&1 | tee /tmp/licomp-tests.txt
