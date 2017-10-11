#!/bin/bash

#
# Load Korean Sentences from a tsv files (made by korean_to_tsv.py) into Anki
#

export PATH="$HOME/bin:$PATH"

# TXT=$1
# TSV=$2
#
SRS_TOOLBELT_ROOT=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki
KEEP=/mnt/data/prg/src/bz/python/sync_google_keep/sync_google_keep_notes

# if [ "$#" -ne 2 ]; then
#     echo "Usage: $0 <KoreanSentences.txt> <korean-sentences.tsv>"
#     exit 1
# fi

convert() {
    TXT=$1
    TSV=$2
    python $SRS_TOOLBELT_ROOT/yatetradki/tools/korean_to_tsv.py $TXT > $TSV
}

update() {
    TSV=$1
    DECK=$2
    PYTHONPATH=$SRS_TOOLBELT_ROOT \
        python2 $SRS_TOOLBELT_ROOT/yatetradki/tools/load_from_csv.py \
            --deck $DECK \
            --model 'KoreanSentences' \
            --fields 'Word,Example,Description,Audio' \
            --csv $TSV --update
}

convert "$KEEP/KoreanSentencesSejong.txt" 'korean-sentences-sejong.tsv'
update 'korean-sentences-sejong.tsv' 'korean::korean-sentences::-sejong'

convert "$KEEP/KoreanSentencesWongwan.txt" 'korean-sentences-wongwan.tsv'
update 'korean-sentences-wongwan.tsv' 'korean::korean-sentences::~wongwan'

