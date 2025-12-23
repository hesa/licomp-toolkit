#!/bin/bash

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$1" == "--local" ]
then
    IMPLEMENTATIONS=../licomp:../licomp-dwheeler:../licomp-hermione:../licomp-osadl:../licomp-reclicense:../licomp-proprietary::../licomp-gnuguide:.
    shift
fi


check_return_value()
{
    ACTUAL=$1
    EXPECTED=$2
    COMMAND="$3"

    if [ $EXPECTED -ne $ACTUAL ]
    then
        echo "ERROR"
        echo "Return values differ"
        echo "  Expected: $EXPECTED"
        echo "  Actual:   $ACTUAL"
        echo "  Command:  $COMMAND"
        exit 1
    fi
}


REPLY_FILE=licomp-toolkit-reply.json


validate_reply()
{
    INBOUND="$1"
    OUTBOUND="$2"
    VERIFY_EXPECTED=$3
    VALIDATE_EXPECTED=$4
    RESOURCE_ARGS="$5"
    PYTHONPATH=$IMPLEMENTAIONS:${PYTHONPATH}:. python3 licomp_toolkit/__main__.py $RESOURCE_ARGS verify -il "$INBOUND" -ol "$OUTBOUND" > $REPLY_FILE
    RET=$?
#    echo " ---------------------------||||| RET: $RET == $VERIFY_EXPECTED"
    printf "%-80s"  "verify -il \"$INBOUND\" -ol \"$OUTBOUND\""
    check_return_value $RET $VERIFY_EXPECTED "verify -il \"$INBOUND\" -ol \"$OUTBOUND\""
    echo " OK"
    
    PYTHONPATH=$IMPLEMENTATIONS:${PYTHONPATH}:. python3 licomp_toolkit/__main__.py validate $REPLY_FILE 
    RET=$?
    printf "\\ %-78s"  "validate -il \"$INBOUND\" -ol \"$OUTBOUND\"" 
    check_return_value $RET $VALIDATE_EXPECTED "validate $REPLY_FILE (verify -il \"$INBOUND\" -ol \"$OUTBOUND\")"
    echo " OK"
}


compatibles()
{
    validate_reply MIT MIT 0 0
    validate_reply MIT BSD-3-Clause 0 0
    validate_reply MIT "BSD-3-Clause OR MIT" 0 0 
    validate_reply "BSD-3-Clause OR MIT" MIT 0 0
    validate_reply "BSD-3-Clause OR MIT" "BSD-2-Clause AND ISC" 0 0 
    validate_reply "BSD-3-Clause OR GPL-2.0-only" "BSD-2-Clause AND ISC" 0 0 
    validate_reply "BSD-3-Clause OR GPL-2.0-only" "BSD-2-Clause AND Apache-2.0" 0 0 
    validate_reply  "BSD-2-Clause OR Apache-2.0" "GPL-2.0-only" 0 0
    validate_reply "Apache-2.0" "GPL-3.0-only" 0 0 
    validate_reply "GPL-3.0-only" "Apache-2.0" 2 0 
}

incompatibles()
{
    validate_reply GPL-2.0-only MIT 2 0
    validate_reply "BSD-3-Clause AND GPL-2.0-only" "BSD-2-Clause AND ISC" 2 0 
    validate_reply "GPL-2.0-only" "BSD-2-Clause AND Apache-2.0" 2 0 
    validate_reply "BSD-3-Clause AND GPL-2.0-only" "BSD-2-Clause AND Apache-2.0" 2 0 
    validate_reply "GPL-2.0-only" "BSD-2-Clause AND Apache-2.0" 2 0 
    validate_reply "BSD-2-Clause AND Apache-2.0" "GPL-2.0-only" 2 0 
    validate_reply "Apache-2.0" "GPL-2.0-only" 2 0
    echo ---------------------------------------------
    validate_reply "Apache-2.0" "GPL-3.0-only" 9 0 " -r all"
}

echo "Compatibles"
#compatibles
echo "Incompatibles"
incompatibles
rm $REPLY_FILE
