#!/bin/bash

while true; do
    python capture.py page.png 600 400;
    python textblock.py page.png;
    montage page.png result.png rect.png -tile 2x3 -geometry +0+0 three.png;
    sleep 1;

done
