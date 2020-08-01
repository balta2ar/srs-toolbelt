#!/bin/bash

IN=${1:-/dev/stdin}
OUT=${2:-/dev/stdout}

DSLS=""
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/en-en/AmericanHeritageDictionary/En-En_American_Heritage_Dictionary.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/en-en/CALD3 for Lingvo/dsl/En-En_Cambridge Advanced Learners Dictionary.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/en-en/MED2 for Lingvo/dsl/En-En_Macmillan English Dictionary.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/en-en/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'"

# Use dictionaries with idioms and phrasal verbs
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/American Heritage Dictionary, 4Ed.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/American Heritage Thesaurus.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/Cambridge compiled idiom dictionary.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/Collins English-Russian Dictionary.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/English Phrasal Verbs.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/English-Russian short Idioms.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/Idioms and Phrasal Verbs EnRu.dsl'"
DSLS+=" --dsl '/mnt/payload/distrib/lang/dictionaries/from_shrekello/dsl_unpacked/McGraw-Hills American Idioms and Phrasal Verbs.dsl'"

#PYTHONPATH=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki \
PYTHONPATH=/home/bz/dev/src/srs-toolbelt \
    eval "python -m yatetradki.reader.dsl $DSLS > $OUT < $IN"
