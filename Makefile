LINGVO_WORDS = data3/test.txt
LINGVO_DECK = data3/test.tsv
DSLS =
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl'
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl'
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'

lingvo:
	python yatetradki/extract/lingvo-online.ru/lingvo-online.py --num-pages 100 > $(LINGVO_WORDS)
	python -m yatetradki.reader.dsl $(DSLS) > $(LINGVO_WORDS) < $(LINGVO_DECK)

ANKI_COLLECTION = /home/bz/Documents/Anki/bz/collection.anki2
ANKI_KOREAN_MODEL = CourseraKoreanBasic
ANKI_KOREAN_DECK = korean::coursera-korean

# $(ARGS) may be defined in the command line, e.g.:
# $ make fill-korean ARGS=--dry-run
fill-korean:
	PYTHONPATH=/usr/share/anki python2 yatetradki/korean/fill_audio.py \
		--collection $(ANKI_COLLECTION) \
		--model-name $(ANKI_KOREAN_MODEL) \
		--deck-name $(ANKI_KOREAN_DECK) \
		--num 1000 $(ARGS)

.PHONY:
	echo "PHONY"
