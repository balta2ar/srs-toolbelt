#!/bin/bash

(
    echo "javascript: "
    cat ./nrkup.js
) | tr '\r\n' '  '
echo
