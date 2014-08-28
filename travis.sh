#!/bin/bash

export PYTHONPATH=$PYTHONPATH:pypy


declare -a STEPS=(
    'py.test testing/ -v'
    'python pypy/rpython/bin/rpython targethippy.py'
);

if [[ "$TRANSLATE" == "true" ]]; then
    python pypy/rpython/bin/rpython targethippy.py
else
    eval "py.test $TESTDIR -v"
fi
