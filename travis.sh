#!/bin/bash

export PYTHONPATH=$PYTHONPATH:pypy

if [[ "$TRANSLATE" == "true" ]]; then
    python pypy/rpython/bin/rpython --batch targethippy.py
else
    eval "py.test $TESTDIR -v"
fi
