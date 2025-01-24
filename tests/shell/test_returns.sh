#!/bin/bash

# SPDX-FileCopyrightText: 2025 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$1" == "--local" ]
then
    IMPLEMENTATIONS=../licomp:../licomp-dwheeler:../licomp-hermione:../licomp-osadl:../licomp-reclicense:../licomp-proprietary::../licomp-gnuguide:.
    shift
fi

dummy_cli()
{
    PYTHONPATH=$IMPLEMENTATIONS:${PYTHONPATH}:. python3 licomp_toolkit/__main__.py $*
}

check_ret()
{
    ACTUAL=$1
    EXPECTED=$2
    ARGS="$3"

    if [ $ACTUAL != $EXPECTED ]
    then
        echo " actual:\"$ACTUAL\" != expected:\"$EXPECTED\" :("
        echo "... try locally using:"
        echo "devel/licomp-toolkit --local $ARGS ; echo \$?"
        exit 1
    fi
}

run_comp_test()
{
    EXP=$1
    shift
    dummy_cli $* > /dev/null 2>&1
    RET=$?
    printf "%-75s" "$*: "
    check_ret $RET $EXP "$*"
    echo "OK"
}

test_verify()
{
    # Success and compatible
    run_comp_test 0 "verify -il BSD-3-Clause -ol GPL-2.0-only"

    # Success and mixed compatibility
    run_comp_test 1 "verify -ol 0BSD -il MS-PL"

    # Success and incompatible
    run_comp_test 2 "verify -il GPL-2.0-only -ol BSD-3-Clause"

    # Success and depends
    run_comp_test 3 "--usecase snippet verify -il GPL-1.0-or-later -ol AGPL-3.0-only"

    # Success and unknown
    run_comp_test 4 "--usecase snippet verify -il MS-PL -ol 0BSD"

    # Failure, since unsupported
    run_comp_test 5 "verify -il HPND -ol Unsupported"

    # Failure, since usecase unsupported
    run_comp_test 6 "--usecase blabla  verify -il GPL-2.0-only -ol BSD-3-Clause"

    # Failure, since provisioning case unsupported
    run_comp_test 7 "--provisioning blabla        verify -il GPL-2.0-only -ol BSD-3-Clause"

    # add modification test once modification is implemented

}

test_missing()
{
    # check missing arguments
    run_comp_test 21 "verify"
    run_comp_test 21 "verify -il GPL-2.0-only"
    run_comp_test 21 "verify -ol GPL-2.0-only"
}

test_illegal()
{
    run_comp_test 23 "verify -il GPL-2.0-only -ol"
    run_comp_test 23 "verify -ol GPL-2.0-only -il"
    run_comp_test 23 "verify -ol -il"
    run_comp_test 23 "verify -il MIT and some more"
    run_comp_test 23 "verify -ol MIT and some more"
    run_comp_test 23 "verify -il MIT and some more -ol GPL-2.0-only"
    run_comp_test 23 "verify -il MIT -ol GPL-2.0-only and some more"
}

test_help()
{
    run_comp_test 0 " --help verify -il MIT -ol GPL-2.0-only"
    run_comp_test 0 " -h verify "
    run_comp_test 0 " -h"
    run_comp_test 0 " --help"
    run_comp_test 0 " verify --help"
    run_comp_test 0 " verify -h"
}

test_with()
{
    run_comp_test 21 "verify -ol MIT -il WITH"
    run_comp_test 21 "verify -ol WITH -il MIT"
    run_comp_test 21 "verify -ol WITH -il WITH"
}    

test_verify
test_missing
test_illegal
test_help
test_with
