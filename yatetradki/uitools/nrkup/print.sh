#!/bin/bash

FILE=$1
(
    echo "javascript: "
    cat ./$FILE
) | tr '\r\n' '  '
echo
