#!/bin/bash

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$1" == "--local" ]
then
    IMPLEMENTATIONS=../licomp:../licomp-dwheeler:../licomp-hermione:../licomp-osadl:../licomp-reclicense:../licomp-proprietary::../licomp-gnuguide:.
    shift
fi

TMP_FILE=licomp_toolkit_test.tmp
TEST_HANDLER=false

run_lt()
{
    PYTHONPATH=$IMPLEMENTATIONS:${PYTHONPATH}:. python3 licomp_toolkit/__main__.py $*
}

err()
{
    echo "$*" 1>&2
}

check_ret()
{
    LICENSES="$1"
    FORMAT=$2
    HANDLER="$3"
    EXP_RET=$4
    printf "%-50s" "-of $FORMAT display-compatibility $LICENSES: "
    run_lt -of $FORMAT display-compatibility  $LICENSES > $TMP_FILE
    if [ "$TEST_HANDLER" = "true" ]
    then
        $HANDLER $TMP_FILE > /dev/null 2>&1
        ACT_RET=$?
        
        if [ $ACT_RET -ne $EXP_RET ]
        then
            
            err "ERROR"
            err " * command:  display-compatibility $LICENSES"
            err " * format:   $FORMAT"
            err " * expected: $EXP_RET"
            err " * actual:   $ACT_RET"
            exit 1
        fi
    fi
    echo OK
}

is_pdf()
{
    PDF_FILE=$1
    IS_PDF=$(file $PDF_FILE | grep PDF | wc -l)
    printf "%-50s " "is pdf: "
    if [ $IS_PDF -eq 0 ]
    then
        err
        err "$PDF_FILE not in PDF format"
        exit 1
    else
        echo OK
    fi
}

check_ret "MIT BSD-3-Clause" "json" "jq ." 0
check_ret "MIT BSD-3-Clause" "json" "dot $TMP_FILE -Tpdf -o tmp.pdf" 1

check_ret "MIT BSD-3-Clause" "dot"  "jq ." 5
check_ret "MIT BSD-3-Clause" "dot"  "dot $TMP_FILE -Tpdf -o tmp.pdf" 0
if [ "$TEST_HANDLER" = "true" ]
then
   is_pdf tmp.pdf
fi
   
