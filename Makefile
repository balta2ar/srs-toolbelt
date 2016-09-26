TEST_IN = data3/test.txt
TEST_OUT = data3/test.tsv
LINGVO_WORDS = data3/lingvolive.txt
LINGVO_DECK = data3/lingvolive.tsv
ENGLISH_WORDS = data3/english.txt
ENGLISH_DECK = data3/english.tsv
PORTUGUESE_WORDS = data3/portuguese.txt
PORTUGUESE_DECK = data3/portuguese.tsv
DSLS =
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl'
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl'
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'

PT_DSLS =
PT_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/por-por/pt/por-por_dic_priberam_an_1_1.dsl'
PT_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/por-por/pt/UniversalPtRu.dsl'
PT_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/por-por/pt/UniversalRuPt.dsl'

TEST_DSLS = --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'

lingvo-online:
	python yatetradki/extract/lingvo-online.ru/lingvo-online.py --num-pages 100 > $(LINGVO_WORDS)
	python -m yatetradki.reader.dsl $(DSLS) > $(LINGVO_DECK) < $(LINGVO_WORDS)

lingvolive:
	python -m yatetradki.reader.dsl $(DSLS) > $(LINGVO_DECK) < $(LINGVO_WORDS)

portuguese:
	python -m yatetradki.reader.dsl $(PT_DSLS) > $(PORTUGUESE_DECK) < $(PORTUGUESE_WORDS)

english:
	python -m yatetradki.reader.dsl $(DSLS) > $(ENGLISH_DECK) < $(ENGLISH_WORDS)

test:
	python -m yatetradki.reader.dsl $(TEST_DSLS) > $(TEST_OUT) < $(TEST_IN)

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
