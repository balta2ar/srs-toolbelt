#!/bin/bash

IN=${1:-/dev/stdin}
OUT=${2:-/dev/stdout}

#BASE="/home/bz/payload/data/dict/norwegian/norwegian-dsl"

DSLS=""
DSLS+=" --dsl '/home/bz/payload/distrib/lang/dictionaries/norwegian/norwegian-dsl/UniversalNoRu.dsl'"
DSLS+=" --dsl '/home/bz/payload/distrib/lang/dictionaries/norwegian/norwegian-dsl/UniversalNoRu_abrv.dsl'"
DSLS+=" --dsl '/home/bz/payload/distrib/lang/dictionaries/norwegian/norwegian-dsl/UniversalRuNo.dsl'"

PYTHONPATH=/mnt/data/prg/src/bz/python/yandex-slovari-tetradki \
    eval "python -m yatetradki.reader.dsl $DSLS > $OUT < $IN"
