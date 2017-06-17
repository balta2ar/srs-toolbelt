srs-toolbelt (former yandex-slovari-tetradki)
=============================================

In this repository I keep all kinds of useful scripts that I use to enhance
my SRS (Spaced Repetition Software, e.g. Anki, Memrise, Quizlet) experience.

Initially this repo was named `yandex-slovari-tetradki` because that's what
the code here used to do. Few years later Yandex.Slovari server was shutdown
and this code got outdated. I slightly adapted it, reworked and now it
helps me with the following reoccuring tasks:

1. Convert a list of new words (taken from a dictionary lookup history) into
   Anki flash cards.
2. Easily add TTS audio for my new Korean words and phrases (powered by Naver
   TTS)
3. Do forced alignment for korean sentences from my Korean textbook and convert
   them to Memrise course (flash cards).

## Information below is outdated

yandex-slovari-tetradki is a script to extract words from Yandex Slovari.Tetradki.
I happen to use this translation service and I thought I could help myself to
memorize new words better. One way to do that is to always keep them in front
of your eyes. This script is supposed to extract last N words and display them
nicely in conky.

## Features

* The service has been closed ~~Extracts and shows your words from Yandex.Slovari copybooks~~ (![https://slovari.yandex.ru](https://slovari.yandex.ru/~%D1%82%D0%B5%D1%82%D1%80%D0%B0%D0%B4%D0%BA%D0%B8/0/))
* Credentials are specified in command-line arguments or in netrc file
* Shows synonyms and antonyms of the word (http://www.thesaurus.com/)
* Shows word definitions (www.thefreedictionary.com)
* The server is down ~~Shows word usage~~ (http://bnc.bl.uk/BLquery.php)
* Color schemes are customized in JSON files
* Request caching reduces number of network requests
* Columned layout

## Usage

```
$ python2 main.py --num-words 3
en -> ru | conform             согласовывать, сообразовывать
     syn : coordinate, reconcile, fit, yield, accommodate, integrate, tailor, attune, harmonize
     ant : refuse, deny, prevent, reject, disagree, oppose, disobey, disregard, ignore, neglect
     def : 1. a.  To be or act in accord with a set of standards, expectations, or specifications:
           a computer that conforms with the manufacturer's advertising claims; students learning
           to conform to school safety rules. See Synonyms at  correspond.b.  To act, often
           unquestioningly, in accordance with traditional customs or prevailing standards: "Our
           table manners ... change from time to time, but the changes are not reasoned out; we
           merely notice and conform" (Mark Twain).
           2.  To be similar in form or pattern: a windy road that conforms to the coastline; a
           shirt that conforms to different body shapes.

en -> ru | funnel              дымовая труба, дымоход
     syn : pour, filter, transmit, siphon, channel, move, pipe, convey, conduct, carry, pass
     ant : fail, lose
     def : 1. a.  A conical utensil having a small hole or narrow tube at the apex and used to
           channel the flow of a substance, as into a small-mouthed container.b.  Something
           resembling this utensil in shape.
           2.  A shaft, flue, or stack for ventilation or the passage of smoke, especially the
           smokestack of a ship or locomotive.
           1.  To take the shape of a funnel.
           2.  To move through or as if through a funnel: tourists funneling slowly through
           customs.
           1.  To cause to take the shape of a funnel.
           2.  To cause to move through or as if through a funnel.

en -> ru | fraudulent          обманный, жульнический
     syn : deceitful, crooked, dishonest, phony, forged, fake, counterfeit, sham, crafty, criminal
     ant : frank, honest, sincere, trustworthy, truthful, moral, real, open, genuine, true
     def : 1.  Engaging in fraud; deceitful.
           2.  Characterized by, constituting, or gained by fraud: fraudulent business practices.
```

## Screenshots of anki

![Card](http://i.imgur.com/ZgsLl68.png)

## Screenshots of conky

### Translation & syn & ant

![Colors](http://i.imgur.com/VbO8REc.png)

### Defs

![Definitions](http://i.imgur.com/gePlqoU.png)

### Usage

Export words from cache into Jinja2-formatted deck:

``` bash
python2 main.py export --cache data/jinja.dat --num-words 3000 --formatter AnkiJinja2 --output jinja-sound.txt
```

Fetch words from Yandex Tetradki account. This service was closed, this is only
left as old reference:

``` bash
python2 main.py fetch --fetcher YandexTetradki --cache data2/jinja.dat --num-words 13000 --timeout 10.0 --jobs 1
```

Fetch idioms from thefreedictionary.com/idioms. This isn't exactly how I did it.
Additionally I had to turn on caching and run the script several times because
thefreedictionary.com banned me for frequent requests.

``` bash
python2 main.py fetch --fetcher Idioms --words-filename idioms.txt --cache idioms-7.dat --num-words 11000 --timeout 10.0 --jobs 1 > idioms.log 2>&1
```

Picture:

![Usage](http://i.imgur.com/eiAk5or.png)

Grab words from lingvo-online.ru and convert them into Anki cards taking
articles from DSL dictionaries:

``` bash
cd yatetradki/extract/lingvo-online.ru
python lingvo-online.py > history.txt

cat yatetradki/extract/lingvo-online.ru/history.txt | python -m yatetradki.reader.dsl \
    --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl' \
    --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl' \
    --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl' \
    > data3/lingvo-online.tsv

```

## Author

(c) 2014-2017 Yuri Bochkarev
