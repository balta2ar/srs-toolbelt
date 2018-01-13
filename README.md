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
- [Screenshots of anki](#screenshots-of-anki)
- [Screenshots of conky](#screenshots-of-conky)
    - [Translation & syn & ant](#translation--syn--ant)
    - [Defs](#defs)
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

I have two primary sources of new words: browser history (I use
www.lingvolive.com dicionary) and history in GoldenDict mobile dictionary (I use
"Save history" feature along with synchronization of that file using BTSync or
Resilio Sync now). Every new word is looked up in several DSL dictionaries by
scripts
[dsl.sh](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/reader/dsl.sh)
and
[dsl.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/reader/dsl.py).
On top of that English pronunciation is added automatically using scripts
[audio.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/tools/audio.py)
and
[load_from_csv.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/tools/load_from_csv.py).
The latter one is a universal CSV loader, it can load into any Anki deck.
`audio.py` is another hack that composes several pieces together: it calls parts
of AwesomeTTS Anki plugin with a hardcoded configuration to obtain english
pronunciation.

The resulting cards look as follows:

![Automatic Card](https://i.imgur.com/af6UiMz.jpg)

If course it's a long screenshot. In Anki only a small parts is displayed but
it's scrollable.

Sample usage: grab words from lingvo-online.ru and convert them into Anki cards
taking articles from DSL dictionaries:

``` bash
cd yatetradki/extract/lingvo-online.ru
python lingvo-online.py > history.txt

cat yatetradki/extract/lingvo-online.ru/history.txt | python -m yatetradki.reader.dsl \
    --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/ru-en/DSL UTF16LE/Ru-En_Mostitsky_Universal.dsl' \
    --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/en-ru/LingvoUniversalEnRu/LingvoUniversalEnRu.dsl' \
    --dsl '/mnt/big_ntfs/distrib/lang/dictionaries/LDOCE5 for Lingvo/dsl/En-En-Longman_DOCE5.dsl' \
    > data3/lingvo-online.tsv

```

## 4. Convert Korean sentences from Google Keep into Anki cards

For me it's convenient to use Google Keep as a source of my data for Anki. For
example, I have a note with the following structure:

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

It's convenient because when I do my Korean studies, I can easily dictate
sentences in both languages into my phone and save it into Google Keep. Later
Google Keep is syncronized onto my computer and I convert the received text file
into an Anki card that looks like this:

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
      --only-log-changes=True \
      --no-duplicate=True \
      --pronunciation korean \
      --filename wg1-9.txt \
      --course-url 'https://www.memrise.com/course/1784675/junggeub-hangugeo-je1-9-gwa/edit/'
```

Sample execution log:

``` text
python ./memrise_sync.py --driver phantomjs upload --only-log-changes --pronunciation korean --filename sample2.txt --course-url 'https://www.memrise.com/course
/1793248/wongwan-2-2-high-priority-bz-words/edit/'
2018-01-04 21:29:22,857 INFO Program arguments: driver="<selenium.webdriver.phantomjs.webdriver.WebDriver (session="29bc6cf0-f17d-11e7-9307-f9bfc90e4e0c")>" only_log_changes=True pronunciation="korean" filename="sample2.txt" course_url="https://www.memrise.com/course/1793248/wongwan-2-2-high-priority-bz-words/edit/"
2018-01-04 21:29:22,857 INFO Applying 12 difference: [DiffActionChangeLevel(level_name='January', new_level_name='1 урок'),
 DiffActionChangeWord(level_name='1 урок', old_pair=WordPair(word='만큼', meaning='такой, как; так же, как; настолько; настолько ..., что; в такой мере ..., что; так ... чтобы; так как, поско
льку; раз'), new_pair=WordPair(word='예매', meaning='предварительная покупка')),
 DiffActionChangeWord(level_name='1 урок', old_pair=WordPair(word='구역', meaning='【區域】 район; сектор; зона; граница'), new_pair=WordPair(word='도착', meaning='прибытие')),
 DiffActionChangeWord(level_name='1 урок', old_pair=WordPair(word='흡연', meaning='【吸煙】 курение'), new_pair=WordPair(word='매표소', meaning='билетная касса')),
 DiffActionChangeLevel(level_name='February', new_level_name='2 урок'),
 DiffActionCreateWord(level_name='2 урок', pair=WordPair(word='식구', meaning='член семьи')),
 DiffActionCreateWord(level_name='2 урок', pair=WordPair(word='스케이트', meaning='коньки')),
 DiffActionCreateWord(level_name='2 урок', pair=WordPair(word='야구', meaning='бейсбол')),
 DiffActionChangeLevel(level_name='March', new_level_name='3 урок'),
 DiffActionCreateWord(level_name='3 урок', pair=WordPair(word='답장', meaning='ответное письмо')),
 DiffActionCreateWord(level_name='3 урок', pair=WordPair(word='답장하다', meaning='отвечать на письмо')),
 DiffActionCreateWord(level_name='3 урок', pair=WordPair(word='우체통', meaning='почтовый ящик'))]
2018-01-04 21:29:22,857 INFO Applying action: "DiffActionChangeLevel(level_name='January', new_level_name='1 урок')"
2018-01-04 21:29:23,252 INFO Applying action: "DiffActionChangeWord(level_name='1 урок', old_pair=WordPair(word='만큼', meaning='такой, как; так же, как; настолько; настолько ..., что; в тако
й мере ..., что; так ... чтобы; так как, поскольку; раз'), new_pair=WordPair(word='예매', meaning='предварительная покупка'))"
2018-01-04 21:29:23,656 INFO Applying action: "DiffActionChangeWord(level_name='1 урок', old_pair=WordPair(word='구역', meaning='【區域】 район; сектор; зона; граница'), new_pair=WordPair(word='도착', meaning='прибытие'))"
2018-01-04 21:29:24,067 INFO Applying action: "DiffActionChangeWord(level_name='1 урок', old_pair=WordPair(word='흡연', meaning='【吸煙】 курение'), new_pair=WordPair(word='매표소', meaning='
билетная касса'))"
2018-01-04 21:29:24,506 INFO Applying action: "DiffActionChangeLevel(level_name='February', new_level_name='2 урок')"
2018-01-04 21:29:24,848 INFO Applying action: "DiffActionCreateWord(level_name='2 урок', pair=WordPair(word='식구', meaning='член семьи'))"
2018-01-04 21:29:26,181 INFO Applying action: "DiffActionCreateWord(level_name='2 урок', pair=WordPair(word='스케이트', meaning='коньки'))"
2018-01-04 21:29:27,501 INFO Applying action: "DiffActionCreateWord(level_name='2 урок', pair=WordPair(word='야구', meaning='бейсбол'))"
2018-01-04 21:29:28,326 INFO Applying action: "DiffActionChangeLevel(level_name='March', new_level_name='3 урок')"
2018-01-04 21:29:28,683 INFO Applying action: "DiffActionCreateWord(level_name='3 урок', pair=WordPair(word='답장', meaning='ответное письмо'))"
2018-01-04 21:29:30,028 INFO Applying action: "DiffActionCreateWord(level_name='3 урок', pair=WordPair(word='답장하다', meaning='отвечать на письмо'))"
2018-01-04 21:29:31,383 INFO Applying action: "DiffActionCreateWord(level_name='3 урок', pair=WordPair(word='우체통', meaning='почтовый ящик'))"
/usr/lib/python3.6/site-packages/urllib3/connectionpool.py:858: InsecureRequestWarning: Unverified HTTPS request is being made. Adding certificate verification is strongly advised. See: http$://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
  InsecureRequestWarning)
2018-01-04 21:29:32,292 INFO Pronunciation server is available, proceeding
2018-01-04 21:29:32,292 INFO Injecting file jquery.min.js
2018-01-04 21:29:32,312 INFO Injecting file userscript_stubs.js
2018-01-04 21:29:32,317 INFO Injecting file memrise_client.js
2018-01-04 21:29:32,323 INFO UserScript JS files have been injected
2018-01-04 21:29:32,323 INFO Sleeping 3.0
2018-01-04 21:29:35,342 INFO Adding pronunciation to level 1 урок
2018-01-04 21:29:35,391 INFO Adding pronunciation to level 2 урок
2018-01-04 21:29:35,419 INFO Clicking AddAudio button (3 more remains)
2018-01-04 21:29:36,819 INFO Clicking AddAudio button (2 more remains)
2018-01-04 21:29:38,015 INFO Clicking AddAudio button (1 more remains)
2018-01-04 21:29:39,240 INFO Adding pronunciation to level 3 урок
2018-01-04 21:29:39,272 INFO Clicking AddAudio button (3 more remains)
2018-01-04 21:29:40,417 INFO Clicking AddAudio button (2 more remains)
2018-01-04 21:29:41,574 INFO Clicking AddAudio button (1 more remains)
2018-01-04 21:29:42,812 INFO Sync has finished
```

<!-- 3. Do forced alignment for korean sentences from my Korean textbook and convert
   them to Memrise course (flash cards). -->

## Screenshots of anki

![Card](http://i.imgur.com/ZgsLl68.png)

## Screenshots of conky

### Translation & syn & ant

![Colors](http://i.imgur.com/VbO8REc.png)

### Defs

![Definitions](http://i.imgur.com/gePlqoU.png)

## Author

(c) 2014-2018 Yuri Bochkarev
