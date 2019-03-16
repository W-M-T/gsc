#!/bin/bash

fails=0
for filename in lexer/*.spl; do
    python3 ../lexer.py $filename>/dev/null 2>&1
    if [ $? -eq 0 ] && [ $filename | tail -c 9 | head -c 4 -eq "fail" ]
    then
        echo "ERROR: Expected file $filename to result in lexer error, but no error was produced."
        ((fails++))
    fi
done

if [ $fails -gt 0 ]
then
    exit 1;
else
    echo "SUCCESS: All of the test files were correctly lexed.";
    exit 0;
fi
