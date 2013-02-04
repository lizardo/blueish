#!/bin/bash
set -e -u

tmpdir=$(mktemp -d)
trap "rm -rf $tmpdir" EXIT

prev_tag=$(git describe --tags --abbrev=0 --candidates=100 HEAD)

function test_all()
{
    #FIXME: hid.yaml needs further work to be usable
    for d in sdp_crash1 sdp_crash2 sdp_crash3 test_sdp_process; do
        ./blueish.py testcases/device_connect.py data/base.yaml data/sdp.yaml data/$d.yaml
    done
}

git archive --format=tar --prefix=code/ $prev_tag | tar -C $tmpdir -xf -
test_all > $tmpdir/orig.py
(cd $tmpdir/code && test_all) > $tmpdir/new.py

diff -Naur $tmpdir/orig.py $tmpdir/new.py
