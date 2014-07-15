#!/bin/bash

export PYTHONPATH=$PYTHONPATH:pypy


declare -a STEPS=(
    'py.test testing/ -v'
    'python pypy/rpython/bin/rpython targethippy.py'
    'py.test test_phpt'
);


for var in "${STEPS[@]}"
do
    echo -e "\n\e[32m#### $var ####\e[0m\n"
    $var
    if [ $? != 0 ]
    then
	exit 1
    fi

done
