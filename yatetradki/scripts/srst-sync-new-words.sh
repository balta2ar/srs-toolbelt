#!/bin/bash

# Sync words from history and from all txt files into a single
# dest file.

if [ "$#" -ne 3 ]; then
    echo "usage: $0 <norwegian | lingvolive | krdict> input-words.txt output-deck.csv"
    exit 1
fi

if ! [[ "$1" =~ ^(norwegian|lingvolive|krdict)$ ]]; then
    echo "Unknown mode: \"$1\". Known modes are \"norwegian\", \"lingvolive\", \"krdict\""
    exit 2
fi

export PATH="$HOME/bin:$PATH"

HOST=$(hostname)
MODE=$1
DEST=$2
TEMP=$DEST.tmp
NEW=$DEST.new

TARGET_WORDS=$NEW #$1
TARGET_DECK=$3
TARGET_DECK_NEW=$3.new

# NOT USED: use dsl.sh in yatetradki/reader/ instead
#
# DSLS=""
# DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl'"
# DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl'"
# DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/AmericanHeritageDictionary/En-En_American_Heritage_Dictionary.dsl'"
# DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/CALD3 for Lingvo/dsl/En-En_Cambridge Advanced Learners Dictionary.dsl'"
# DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/MED2 for Lingvo/dsl/En-En_Macmillan English Dictionary.dsl'"
# DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'"

# if [ "$#" -ne 2 ]; then
#     echo "Usage: $0 <words.txt> <deck.csv>"
#     exit 1
# fi

merge() {
    $HOME/.local/bin/srst-get-words-from-browser-history.sh $MODE > "browser.$MODE.$HOST.txt"
    cat *.txt | sort -u > $TEMP
    if [ ! -e "$DEST" ]; then
        echo -n "" > "$DEST"
    fi
    comm -1 -3 $DEST $TEMP > $NEW
    cat $NEW
}

convert() {
    echo -n "" > "$TARGET_DECK_NEW"

    if [ "$MODE" == "lingvolive" ]; then

        # PYTHONPATH=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki \
        #     eval "python -m yatetradki.reader.dsl $DSLS > $TARGET_DECK_NEW < $TARGET_WORDS"
        # bash /mnt/data/prg/src/bz/python/yandex-slovari-tetradki/yatetradki/reader/dsl.sh \
        #     "$TARGET_WORDS" "$TARGET_DECK_NEW"
        $HOME/.local/bin/srst-dsl-english.sh "$TARGET_WORDS" "$TARGET_DECK_NEW"

    elif [ "$MODE" == "norwegian" ]; then

        $HOME/.local/bin/srst-dsl-norwegian.sh "$TARGET_WORDS" "$TARGET_DECK_NEW"

    elif [ "$MODE" == "krdict" ]; then

        python /mnt/data/prg/src/bz/python/yandex-slovari-tetradki/yatetradki/korean/krdict_to_tsv.py \
            "$TARGET_WORDS" "$TARGET_DECK_NEW"

    fi

    cat "$TARGET_DECK_NEW" >> "$TARGET_DECK"
}

update() {
    if [ "$MODE" == "lingvolive" ]; then

        # A single script can both add from csv and English audio.
        # Note that if you need Korean audio, make sure to remove --audio
        # argument and use a different script fill_audio.py as below.
        # PYTHONPATH=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki \
        #     python2 /mnt/data/prg/src/bz/python/yandex-slovari-tetradki/yatetradki/tools/load_from_csv.py \
        $HOME/.local/bin/srst-load-from-csv \
            --deck 'english::lingvo-online::-new' \
            --model 'LingvoOnline' \
            --fields 'Word,Example,Description,Audio' \
            --csv $TARGET_DECK_NEW --update --audio english
            #--csv $MODE.csv.new --audio --update

    elif [ "$MODE" == "norwegian" ]; then

        $HOME/.local/bin/srst-load-from-csv \
            --deck 'norwegian::auto-import::-new' \
            --model 'NorwegianAutoImport' \
            --fields 'Word,Example,Description,Audio' \
            --csv $TARGET_DECK_NEW --update --audio norwegian

    elif [ "$MODE" == "krdict" ]; then

        DECK='korean::krdict-korean-go-kr::-new'
        MODEL='KrdictKoreanGoKr'

        # Same as previous but without audio. Korean audio is added using
        # another script.
        PYTHONPATH=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki \
            python2 /mnt/data/prg/src/bz/python/yandex-slovari-tetradki/yatetradki/tools/load_from_csv.py \
                --deck $DECK \
                --model $MODEL \
                --fields 'Word,Example,Description,Audio' \
                --csv $TARGET_DECK_NEW --update
                #--csv $MODE.csv.new --update

        # Now add Korean audio.
        # --dry-run \
        PYTHONPATH=/usr/share/anki \
            python2 /mnt/data/prg/src/bz/python/yandex-slovari-tetradki/yatetradki/korean/fill_audio.py \
            --collection '/home/bz/Documents/Anki/bz/collection.anki2' \
            --model-name $MODEL \
            --deck-name $DECK \
            --korean-word-field Word \
            --translated-word-field Description \
            --korean-audio-field Audio \
            --num 1000

    fi
}

telegram_notify() {
    MESSAGE=$1
    echo curl -X POST "https://api.telegram.org/bot$TELEGRAM_ACCESS_TOKEN/sendMessage" -d "chat_id=$TELEGRAM_CHAT_ID&text=$MESSAGE"
    curl -X POST "https://api.telegram.org/bot$TELEGRAM_ACCESS_TOKEN/sendMessage" -d "chat_id=$TELEGRAM_CHAT_ID&text=$MESSAGE"
}

merge
if [ -s $NEW ]; then
    set -e
    convert
    sort -u -o $TARGET_DECK $TARGET_DECK
    update
    mv $TEMP $DEST

    telegram_notify "$(echo -e "Mode: $MODE\n"; cat $NEW)"
    #torsocks ~/bin/telegram.py --message "$(cat $NEW)"
fi
