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
    EXPEXcTED=$1
    ACTUAL=$2
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
    EXPECTED=$3
    PYTHONPATH=$IMPLEMENTATIONS:${PYTHONPATH}:. python3 licomp_toolkit/__main__.py verify -il "$INBOUND" -ol "$OUTBOUND" > $REPLY_FILE
    PYTHONPATH=$IMPLEMENTATIONS:${PYTHONPATH}:. python3 licomp_toolkit/__main__.py validate $REPLY_FILE 
    RET=$?
    printf "%-75s"  "reply from  verify -il \"$INBOUND\" -ol \"$OUTBOUND\"" 
    check_return_value $RET $EXPECTED "validate $REPLY_FILE (verify -il \"$INBOUND\" -ol \"$OUTBOUND\")"
    echo OK
}

validate_reply MIT MIT 0
validate_reply MIT BSD-3-Clause 0
validate_reply MIT "BSD-3-Clause OR MIT" 0
validate_reply "BSD-3-Clause OR MIT" MIT 0
validate_reply "BSD-3-Clause OR MIT" "X11 AND ISC" 0

exit
rm $REPLY_FILE
