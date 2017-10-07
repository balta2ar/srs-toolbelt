#!/bin/bash

#
# Load Korean Sentences from a tsv files (made by korean_to_tsv.py) into Anki
#

export PATH="$HOME/bin:$PATH"

# HOST=$(hostname)
TXT=$1
TSV=$2

SRS_TOOLBELT_ROOT=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <KoreanSentences.txt> <korean-sentences.tsv>"
    exit 1
fi

merge() {
    $HOME/bin/words-from-history.sh lingvolive > $HOST.txt
    cat *.txt | sort -u > $TEMP
    if [ ! -e "$DEST" ]; then
        echo -n "" > "$DEST"
    fi
    comm -1 -3 $DEST $TEMP > $NEW
    cat $NEW
}

convert() {
    python $SRS_TOOLBELT_ROOT/yatetradki/tools/korean_to_tsv.py $TXT > $TSV
}

update() {
    PYTHONPATH=$SRS_TOOLBELT_ROOT \
        python2 $SRS_TOOLBELT_ROOT/yatetradki/tools/load_from_csv.py \
            --deck 'korean::korean-sentences' \
            --model 'KoreanSentences' \
            --fields 'Word,Example,Description,Audio' \
            --csv $TSV #--update
}

# convert
update

# merge
# if [ -s $NEW ]; then
#     set -e
#     convert
#     sort -u -o $ENGLISH_DECK $ENGLISH_DECK
#     update
#     mv $TEMP $DEST
# fi
