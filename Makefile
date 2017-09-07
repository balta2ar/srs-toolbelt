TEST_IN = data3/test.txt
TEST_OUT = data3/test.tsv
LINGVO_WORDS = data3/lingvolive.txt
LINGVO_DECK = data3/lingvolive.tsv
ENGLISH_WORDS = data3/english.txt
ENGLISH_DECK = data3/english.tsv
#ENGLISH_WORDS = toefl/words.txt
#ENGLISH_DECK = toefl/from_dsl.tsv
PORTUGUESE_WORDS = data3/portuguese.txt
PORTUGUESE_DECK = data3/portuguese.tsv
DSLS =
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl'
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl'
DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'

PT_DSLS =
PT_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/por-por/pt/por-por_dic_priberam_an_1_1.dsl'
PT_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/por-por/pt/UniversalPtRu.dsl'
PT_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/por-por/pt/UniversalRuPt.dsl'

TEST_DSLS = --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'

MORE_DSLS =
MORE_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl'
MORE_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl'
MORE_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/CALD3 for Lingvo/dsl/En-En_Cambridge Advanced Learners Dictionary.dsl'
MORE_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/MED2 for Lingvo/dsl/En-En_Macmillan English Dictionary.dsl'
MORE_DSLS += --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-en/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl'

SAT_WORDS = data3/sat-words.txt
SAT_DECK = data3/sat-words.tsv
# SAT_WORDS = data3/sat-words-test.txt
# SAT_DECK = data3/sat-words-test.tsv
sat-words:
	python -m yatetradki.reader.dsl $(MORE_DSLS) > $(SAT_DECK) < $(SAT_WORDS)

lingvo-online:
	python yatetradki/extract/lingvo-online.ru/lingvo-online.py --num-pages 100 > $(LINGVO_WORDS)
	python -m yatetradki.reader.dsl $(DSLS) > $(LINGVO_DECK) < $(LINGVO_WORDS)

lingvolive:
	python -m yatetradki.reader.dsl $(DSLS) > $(LINGVO_DECK) < $(LINGVO_WORDS)

portuguese:
	python -m yatetradki.reader.dsl $(PT_DSLS) > $(PORTUGUESE_DECK) < $(PORTUGUESE_WORDS)

TEMP_WORDS = /tmp/words.txt
SHARED_WORDS = /home/bz/share/btsync/everywhere/info/words/lingvolive-work.txt
LOCAL_WORDS = /home/bz/share/btsync/everywhere/info/words/lingvolive-home.txt
#LOCAL_WORDS = data3/lingvolive-home.txt
english-words:
	cp $(ENGLISH_WORDS) "$(ENGLISH_WORDS).`date +%FT%T`.txt"
	words-from-history.sh lingvolive > $(LOCAL_WORDS)
	cat $(LOCAL_WORDS) $(SHARED_WORDS) $(ENGLISH_WORDS) | sort -u > $(TEMP_WORDS)
	echo "New words:"
	comm -13 $(ENGLISH_WORDS) $(TEMP_WORDS)
	echo "Removed words:"
	comm -23 $(ENGLISH_WORDS) $(TEMP_WORDS)
	cat $(TEMP_WORDS) | sort -u > $(ENGLISH_WORDS)

english:
	python -m yatetradki.reader.dsl $(DSLS) > $(ENGLISH_DECK) < $(ENGLISH_WORDS)

test:
	python -m yatetradki.reader.dsl $(TEST_DSLS) > $(TEST_OUT) < $(TEST_IN)

ANKI_COLLECTION = /home/bz/Documents/Anki/bz/collection.anki2
ANKI_KOREAN_MODEL = CourseraKoreanBasic
ANKI_KOREAN_DECK = korean::coursera-korean

# $(ARGS) may be defined in the command line, e.g.:
# $ make fill-korean ARGS=--dry-run
fill-korean-audio:
	PYTHONPATH=/usr/share/anki python2 yatetradki/korean/fill_audio.py \
		--collection $(ANKI_COLLECTION) \
		--model-name $(ANKI_KOREAN_MODEL) \
		--deck-name $(ANKI_KOREAN_DECK) \
		--num 1000 $(ARGS)

fill-sejong-audio:
	PYTHONPATH=/usr/share/anki python2 yatetradki/korean/fill_audio.py \
		--collection $(ANKI_COLLECTION) \
		--model-name 'Sejong-1-3cards' \
		--deck-name 'korean::sejong-1' \
		--korean-word-field KoreanWord \
		--translated-word-field TranslatedWord \
		--korean-audio-field KoreanAudio \
		--num 1000 $(ARGS)

fill-wongwan-audio:
	PYTHONPATH=/usr/share/anki python2 yatetradki/korean/fill_audio.py \
		--collection $(ANKI_COLLECTION) \
		--model-name 'WonGwan-3' \
		--deck-name 'korean::wongwan-1-1' \
		--korean-word-field KoreanWord \
		--translated-word-field TranslatedWord \
		--korean-audio-field KoreanAudio \
		--num 1000 $(ARGS)

.PHONY:
	echo "PHONY"
