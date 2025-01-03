#!/bin/bash

# SPDX-FileCopyrightText: 2024 Henrik Sandklef
#
# SPDX-License-Identifier: GPL-3.0-or-later

LT_VERSION=$(grep licomp_toolkit_version licomp_toolkit/config.py | cut -d = -f 2 | sed "s,[' ]*,,g")

if [ "$1" == "--local" ]
then
    IMPLEMENTATIONS=../licomp:../licomp-dwheeler:../licomp-hermione:../licomp-osadl:../licomp-reclicense:../licomp-proprietary::../licomp-gnuguide:.
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

test_licomp_tk_text() {
    COMMAND="$1"
    EXTRA_COMMAND="$2"
    EXP="$3"

    echo -n "$COMMAND: "
    ACTUAL=$(echo PYTHONPATH=$IMPLEMENTATIONS:. ./licomp_toolkit/__main__.py $COMMAND $EXTRA_COMMAND | bash)

    if [ "$EXP" != "$ACTUAL" ]
    then
	echo "Fail"
	echo "  expected: $EXP"
	echo "  actual:   $ACTUAL"
	echo "  command:  $COMMAND"
	echo "  extra:    $EXTRA_COMMAND"
        echo "  command:  devel/licomp-toolkit $COMMAND"
	exit 1
    fi
    echo OK
}

test_version()
{
    echo "# test version"
    test_licomp_tk_text "--version" "" "$LT_VERSION"
    test_licomp_tk_text "--name" "" licomp-toolkit
    test_licomp_tk_text "versions" "| head -1" "licomp-toolkit:$LT_VERSION"
    test_licomp_tk_text "versions" "| wc -l" "7"
}

test_supp_unsupp()
{
    echo "# test supported/unsupported licenses"
    test_licomp_tk "verify -il MIT -ol MIT" ".summary.results.yes.count" 4
    test_licomp_tk "verify -il MIT -ol MIT2" ".summary.results.nr_valid" 0
    test_licomp_tk "verify -il MIT2 -ol MIT" ".summary.results.nr_valid" 0
    test_licomp_tk "verify -il MIT2 -ol MIT2" ".summary.results.nr_valid" 0
}

test_snippets()
{
    echo "# test snippets only"
    test_licomp_tk "-u snippet verify -il MIT -ol MIT" ".summary.results.nr_valid" 2
    test_licomp_tk "-u snippet verify -il MIT -ol MIT2" ".summary.results.nr_valid" 0
    test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.nr_valid" 2
    test_licomp_tk "-u snippet verify -il LGPL-2.1-or-later -ol BSD-3-Clause" ".summary.results.nr_valid" 2
    test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.yes.count" 2
    test_licomp_tk "-u snippet verify -il LGPL-2.1-or-later -ol BSD-3-Clause" ".summary.results.yes.count" null
}

test_snippet_bindist()
{
    echo "# snippet vs bin dist"
    test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.nr_valid" 2
    test_licomp_tk "-u snippet verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.yes.count" 2
    test_licomp_tk "verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.nr_valid" 3
    test_licomp_tk "verify -il BSD-3-Clause -ol LGPL-2.1-or-later" ".summary.results.yes.count" 3
}

test_supports_license()
{
    echo "# supports license"
    test_licomp_tk_text " -of text supports-license MIT" " | wc -l" 6
    test_licomp_tk_text " -of json supports-license MIT" " | jq .[] | wc -l" 6
    test_licomp_tk_text " supports-license MIT" " | jq .[] | wc -l" 6
}

test_supports_provisioning()
{
    echo "# supports provisioning"
    test_licomp_tk_text " -of text supports-provisioning binary-distribution" " | wc -l" 6
    test_licomp_tk_text " -of text supports-provisioning provide-webui" " | grep -v \"^$\" | wc -l " 0
}

test_supports_usecase()
{
    echo "# supports usecase"
    test_licomp_tk_text " -of text supports-usecase snippet" " | wc -l" 2
    test_licomp_tk_text " -of text supports-usecase library" " | wc -l " 4
}


test_version
test_supp_unsupp
test_snippets
test_snippet_bindist
test_supports_license
test_supports_provisioning
test_supports_usecase

