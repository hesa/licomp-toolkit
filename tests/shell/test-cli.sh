#!/bin/bash

# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

if [ "$1" == "--local" ]
then
    IMPLEMENTATIONS=../licomp:../licomp-dwheeler:../licomp-hermione:../licomp-osadl:../licomp-reclicense:../licomp-proprietary:.
    shift
fi

licomp_tk() {
    PYTHONPATH=$IMPLEMENTATIONS:. ./licomp_toolkit/__main__.py $*
}

test_licomp_tk() {
    COMMAND="$1"
    JQ_ARGS="$2"
    EXP="$3"

    echo -n "$COMMAND: "
    ACTUAL=$(licomp_tk $COMMAND | jq -r $JQ_ARGS)

    if [ "$EXP" != "$ACTUAL" ]
    then
	echo "Fail"
	echo "  expected: $EXP"
	echo "  actual:   $ACTUAL"
	echo "  command:  $COMMAND"
	echo "  jq:       $JQ_ARGS"
        echo "  command:  devel/licomp-toolkit $COMMAND | jq $JQ_ARGS"
	exit 1
    fi
    echo OK
}

echo "# test supported/unsupported licenses"
test_licomp_tk "verify -il MIT -ol MIT" ".summary.results.yes.count" 3
test_licomp_tk "verify -il MIT -ol MIT2" ".summary.results.nr_valid" 0
test_licomp_tk "verify -il MIT2 -ol MIT" ".summary.results.nr_valid" 0
test_licomp_tk "verify -il MIT2 -ol MIT2" ".summary.results.nr_valid" 0

echo "# test snippets only"
test_licomp_tk "-u snippet verify -il MIT -ol MIT" ".summary.results.nr_valid" 2
test_licomp_tk "-u snippet verify -il MIT -ol MIT2" ".summary.results.nr_valid" 0
test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.nr_valid" 2
test_licomp_tk "-u snippet verify -il LGPL-2.1-or-later -ol BSD-3-Clause" ".summary.results.nr_valid" 2
test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.yes.count" null
test_licomp_tk "-u snippet verify -il LGPL-2.1-or-later -ol BSD-3-Clause" ".summary.results.yes.count" 2

echo "# snippet vs bin dist"
test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.nr_valid" 2
test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.no.count" 2
test_licomp_tk "verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.nr_valid" 2
test_licomp_tk "verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.yes.count" 2

