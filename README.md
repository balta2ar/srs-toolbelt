srs-toolbelt (former yandex-slovari-tetradki)
=============================================

## Contents

<!-- TOC -->

- [Contents](#contents)
- [Intro](#intro)
- [1. Sync local Anki DB with ankiweb](#1-sync-local-anki-db-with-ankiweb)
- [2. Print recent hard cards from Anki DB](#2-print-recent-hard-cards-from-anki-db)
- [3. Convert a list of new English words into Anki flash cards.](#3-convert-a-list-of-new-english-words-into-anki-flash-cards)
- [4. Convert Korean sentences from Google Keep into Anki cards](#4-convert-korean-sentences-from-google-keep-into-anki-cards)
- [5. Easily add pronunciation to Korean words in Memrise](#5-easily-add-pronunciation-to-korean-words-in-memrise)
- [6. Convert Google Keep note with Korean words into Memrise course with pronunciation](#6-convert-google-keep-note-with-korean-words-into-memrise-course-with-pronunciation)
- [Information below is outdated](#information-below-is-outdated)
- [Features](#features)
- [Usage](#usage)
- [Screenshots of anki](#screenshots-of-anki)
- [Screenshots of conky](#screenshots-of-conky)
    - [Translation & syn & ant](#translation--syn--ant)
    - [Defs](#defs)
    - [Usage](#usage-1)
- [Author](#author)

<!-- /TOC -->

## Intro

In this repository I keep all kinds of useful scripts that I use to enhance
my SRS (Spaced Repetition Software, e.g. Anki, Memrise, Quizlet) experience.

Initially this repo was named `yandex-slovari-tetradki` because that's what
the code here used to do. Few years later Yandex.Slovari server was shutdown
and this code got outdated. I slightly adapted it, reworked and now it
helps me with the following reoccuring tasks.

## 1. Sync local Anki DB with ankiweb

Script [anki_sync.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/tools/anki_sync.py) syncronizes my local Anki DB with the remote version. Nothing extraordinary, I just looked at Anki internals and tried to come up with a minimal code that would automatically run the sync without starting the GUI manually.


## 2. Print recent hard cards from Anki DB

I find it occasionally useful to display Anki cards that I answered "Hard" on my desktop. To do that, I use script [recent.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/tools/recent.py) to print out recent cards. To squeeze more words into the space, words are printed in multiple columns.

![Recent](https://i.imgur.com/9yDSeui.png)

Because I have many decks, not all of them are queried. I have the following file that contains the decks that I only want to see in the output of this script:

``` text
$ cat recent_queries.txt
deck:english::english-for-students rated:7:2    Word
deck:english::englishclub-phrasal-verbs rated:7:2       Word
deck:english::idiomconnection rated:7:2 Word
deck:english::jinja rated:7:2   Word
deck:english::lingvo-online rated:7:2   Word
deck:english::phrases-org-uk rated:7:2  Word
deck:english::sat-words rated:7:2       Word
deck:english::toefl-vocabulary rated:7:2        Word
deck:english::using-english rated:7:2   Word
```

## 3. Convert a list of new English words into Anki flash cards.

I have two primary sources of new words: browser history (I use www.lingvolive.com dicionary) and history in GoldenDict mobile dictionary (I use "Save history" feature along with synchronization of that file using BTSync or Resilio Sync now). Every new word is looked up in several DSL dictionaries by scripts [dsl.sh](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/reader/dsl.sh) and [dsl.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/reader/dsl.py). On top of that English pronunciation is added automatically using scripts [audio.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/tools/audio.py) and [load_from_csv.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/tools/load_from_csv.py). The latter one is a universal CSV loader, it can load into any Anki deck. `audio.py` is another hack that composes several pieces together: it calls parts of AwesomeTTS Anki plugin with a hardcoded configuration to obtain english pronunciation.

The resulting cards look as follows:

![Automatic Card](https://i.imgur.com/af6UiMz.jpg)

If course it's a long screenshot. In Anki only a small parts is displayed but it's scrollable.

## 4. Convert Korean sentences from Google Keep into Anki cards

For me it's convenient to use Google Keep as a source of my data for Anki. For example, I have a note with the following structure:

``` text
# Глава 8, 공공 예절

* 그러면 휴대 전화로 사진을 찍으면 안 됩니까?
* 네, 안 됩니다. 휴대 전화는 전원을 꺼 주세요.
Тогда делать фотографии телефоном нельзя?
Да, нельзя. Пожалуйста выключите питание телефона.

— 여기서 휴대전화를 사용하면 안  돼요.
— 네, 알겠습니다.
Здесь нельзя пользоваться мобильным телефоном.
Вас понял.
```

It's convenient because when I do my Korean studies, I can easily dictate sentences in both languages into my phone and save it into Google Keep. Later Google Keep is syncronized onto my computer and I convert the received text file into an Anki card that looks like this:

![korean-sentences](https://i.imgur.com/2zXaqad.jpg)

## 5. Easily add pronunciation to Korean words in Memrise

Using [memrise_client.js](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/korean/memrise_client.js) with Tampermonkey as a client and [memrise_server.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/korean/memrise_server.py) and [fill_audio.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/korean/fill_audio.py) as a server I managed to make it very easy to add Korean pronunciation to my Memrise decks. I just need to expand necessary levels on Memrise website and click AddAudio bottons or that button on the header of the page. These buttons are added by the Tampermonkey extension. Backend part uses Flask for REST API and a collection of mp3 files plus NaverTTS to produce pronunciation for the requested korean word.

![Memrise Add Audio](https://i.imgur.com/uDOtwDR.png)

## 6. Convert Google Keep note with Korean words into Memrise course with pronunciation

I have a note with the following structure:

``` text
# 1 урок

@a comment
예매; предварительная покупка
도착; прибытие
매표소; билетная касса

# 2 урок

식구; член семьи
스케이트; коньки
야구; бейсбол

# 3 урок

답장; ответное письмо
답장하다; отвечать на письмо
우체통; почтовый ящик

```

Using [memrise_sync.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/korean/memrise_sync.py) I can easily convert this text into a Memrise course. Basically it syncs this file with Memrise server and adds/removes necessary levels and words in each level. If it detects that `memrise_server.py` is running, it will also inject `memrise_client.js` into the running browser instances and will add pronunciation as well. Sync can be run as follows:

``` bash
python ./memrise_sync.py \
      --driver phantomjs \
      upload \
      --filename wg1-9.txt \
      --course-url 'https://www.memrise.com/course/1784675/junggeub-hangugeo-je1-9-gwa/edit/'
```

<!-- 3. Do forced alignment for korean sentences from my Korean textbook and convert
   them to Memrise course (flash cards). -->

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

(c) 2014-2018 Yuri Bochkarev
