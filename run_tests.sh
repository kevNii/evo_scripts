#!/bin/bash
read -p "Delete existing statistics.csv? (y/N)" -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    rm evosuite-report/statistics.csv && echo "statistics.csv deleted."
fi
echo "Starting tests detached..."
( python3 run_tests.py 1> testruns/output.log 2> testruns/error.log ) &
echo "Tests should be running now"

