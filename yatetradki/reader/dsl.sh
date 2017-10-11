#!/bin/bash

IN=${1:-/dev/stdin}
OUT=${2:-/dev/stdout}

DSLS=""
DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl'"
DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl'"
DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/AmericanHeritageDictionary/En-En_American_Heritage_Dictionary.dsl'"
DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/CALD3 for Lingvo/dsl/En-En_Cambridge Advanced Learners Dictionary.dsl'"
DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/MED2 for Lingvo/dsl/En-En_Macmillan English Dictionary.dsl'"
DSLS+=" --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'"

PYTHONPATH=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki \
    eval "python -m yatetradki.reader.dsl $DSLS > $OUT < $IN"
