#!/bin/bash

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$1" == "--local" ]
then
    export IMPLEMENTATIONS=../licomp:../licomp-dwheeler:../licomp-hermione:../licomp-osadl:../licomp-reclicense:../licomp-proprietary::../licomp-gnuguide:.
    shift
fi
comment_file_presence()
{
    EXPECTED="$1"
    REPORT=$2
    PRESENT=$(grep -c -e "$EXPECTED" $REPORT)
    ACTUAL=$(grep -e "$EXPECTED" $REPORT)
    MSG="$3"
    if [ $PRESENT -ne 1 ]
    then
        echo "ERROR"
        echo "Values differ"
        echo "  Expected:  $EXPECTED"
        #echo "  Actual:   $ACTUAL"
        echo "  Message:   $MSG"
        echo "  Reproduce: grep -e \"$EXPECTED\" $REPORT"
        exit 1
    fi
    
}


licomp-toolkit-verify()
{
    INBOUND="$1"
    OUTBOUND="$2"
    
    PYTHONPATH=$IMPLEMENTATIONS::. python3 licomp_toolkit/__main__.py --verbose $RESOURCE_ARGS verify -il "$INBOUND" -ol "$OUTBOUND" 
}

licomp-toolkit-apply()
{
    OUTPUT_ARGS="$1"
    REPORT="$2"
    
    PYTHONPATH=$IMPLEMENTATIONS::. python3 licomp_toolkit/__main__.py --verbose $RESOURCE_ARGS $OUTPUT_ARGS apply-license-policy $REPORT
}

#
# Text output
#
licomp-toolkit-verify MIT MIT  > report.json
licomp-toolkit-apply " -of text" report.json > policy-report.txt
comment_file_presence "preferred inbound:[ ]*MIT" policy-report.txt "test 1.1"
comment_file_presence "preferred outbound:[ ]*MIT" policy-report.txt "test 1.2"
comment_file_presence "^compatibility:[ ]*yes" policy-report.txt "test 1.5"
comment_file_presence "compatibility details:" policy-report.txt "test 1.6"

licomp-toolkit-verify MIT "MIT OR LGPL-2.1-only"  > report.json
licomp-toolkit-apply " -of text" report.json > policy-report.txt
comment_file_presence "preferred inbound:[ ]*MIT" policy-report.txt "test 2.1"
comment_file_presence "preferred outbound:[ ]*MIT" policy-report.txt "test 2.2"
comment_file_presence "^compatibility:[ ]*yes" policy-report.txt "test 2.5"

