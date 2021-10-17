srs-toolbelt (former yandex-slovari-tetradki)
=============================================

## Contents

<!-- TOC -->

- [srs-toolbelt (former yandex-slovari-tetradki)](#srs-toolbelt-former-yandex-slovari-tetradki)
  - [Contents](#contents)
  - [Intro](#intro)
  - [1. Sync local Anki DB with ankiweb](#1-sync-local-anki-db-with-ankiweb)
  - [2. Print recent hard cards from Anki DB](#2-print-recent-hard-cards-from-anki-db)
  - [3. Convert a list of new English words into Anki flash cards.](#3-convert-a-list-of-new-english-words-into-anki-flash-cards)
  - [4. Convert Korean sentences from Google Keep into Anki cards](#4-convert-korean-sentences-from-google-keep-into-anki-cards)
  - [5. Easily add pronunciation to Korean words in Memrise](#5-easily-add-pronunciation-to-korean-words-in-memrise)
  - [6. Convert Google Keep note with Korean words into Memrise course with pronunciation](#6-convert-google-keep-note-with-korean-words-into-memrise-course-with-pronunciation)
  - [7. Do forced alignment for korean sentences from my Korean textbook and convert them to Memrise course (flash cards).](#7-do-forced-alignment-for-korean-sentences-from-my-korean-textbook-and-convert-them-to-memrise-course-flash-cards)
  - [8. Multi-sourced UI for several norwegian dictionaries](#8-multi-sourced-ui-for-several-norwegian-dictionaries)
  - [My decks](#my-decks)
    - [Anki](#anki)
    - [Memrise](#memrise)
  - [Screenshots of anki](#screenshots-of-anki)
  - [Screenshots of conky](#screenshots-of-conky)
    - [Translation & syn & ant](#translation--syn--ant)
    - [Defs](#defs)
  - [Related materials](#related-materials)
  - [Theory and methods](#theory-and-methods)
    - [SRS Flash Cards](#srs-flash-cards)
    - [Method by Anastasia Kuznetsova](#method-by-anastasia-kuznetsova)
    - [Method by Maru Kachko](#method-by-maru-kachko)
    - [Goldlist method](#goldlist-method)
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

## 7. Do forced alignment for korean sentences from my Korean textbook and convert them to Memrise course (flash cards).

TODO.

## 8. Multi-sourced UI for several norwegian dictionaries

![page1](https://i.imgur.com/JKmHrHA.png)
![page2](https://i.imgur.com/Q82LjRK.png)
![page3](https://i.imgur.com/woKdYHJ.png)

This script [ordbok_uib_no.py](https://github.com/balta2ar/srs-toolbelt/blob/master/yatetradki/uitools/ordbok_uib_no.py) collects the output from multiple sources in a condensed nice format so that you get quick access to dictionary articles as you type. Results are cached, so servers are not stressed. Currently supported sources:

Page 1:
* Inflections from https://ordbok.uib.no/
* Nor, Rus, Eng from https://lexin.oslomet.no/#/findwords/message.bokmal-russian
* Nor->Rus / Rus-Nor direction from https://nb.glosbe.com/nb/ru/
* Nor->Eng direction from https://nb.glosbe.com/nb/en/

Page 2:
* Definitions from https://ordbok.uib.no/
* Definitions from https://naob.no/

Page 3:
* Definitions from https://no.wiktionary.org/wiki/
* Definitions from https://dictionary.cambridge.org/dictionary/english-norwegian/

**Shortcuts**: switch between pages with `Alt-!`, `Alt-@`, `Alt-#` (weird shortcuts are convenient in my layout).

## My decks

### Anki

Here are my Anki decks: [Anki decks](https://yadi.sk/d/8fycApLs3KDE5K)

They are a collection that I've gathered from various sites over the years and
that I'm currently steadily studying. There are about 40000 cards including
words, phrasal verbs, expressions, idioms, phrases and so on.

Most of my Anki collection contains English cards. I also have few decks in
Korean, but it's really nothing to write home about, so I'm not sharing. If
you're still interested, let me know.

### Memrise

Here are my Memrise courses:

[Baltazar Korean
Words](https://www.memrise.com/course/1344980/baltazar-korean-words/) &mdash; I
made this deck during my first year of studies at [Won Gwan](http://wonkwang.ru).

[WonGwan 2-1 High Priority Bz Words](https://www.memrise.com/course/1630943/wongwan-2-1-high-priority-bz-words/),
[WonGwan 2-2 High Priority Bz Words](https://www.memrise.com/course/1793248/wongwan-2-2-high-priority-bz-words/) &mdash;
these two decks were made during the second year of my studies at WonGwan.

[중급 한국어 제1-9 과](https://www.memrise.com/course/1784675/junggeub-hangugeo-je1-9-gwa/) &mdash;
this isn't my piece of work, I simply merged two decks together, [중급 한국어 제1-5 과](https://www.memrise.com/course/653322/1-5-7/) and 
[중급 한국어 제6-9 과](https://www.memrise.com/course/751253/6-9-6/).

These two: [4 Седжон](https://www.memrise.com/course/1197169/4-sedzhon/),
[5 Седжон](https://www.memrise.com/course/1336543/5-sedzhon/) are not mine,
I simply helped to add Korean pronunciation.

Same with these: [Gauss webtoon word list](https://www.memrise.com/course/905498/gauss-webtoon-word-list/),
[HowtoStudyKorean.com Unit 1](https://www.memrise.com/course/150816/howtostudykoreancom-unit-1-2/) &mdash;
I only helped course authors add complete pronunciation in Korean.

## Screenshots of anki

![Card](http://i.imgur.com/ZgsLl68.png)

## Screenshots of conky

### Translation & syn & ant

![Colors](http://i.imgur.com/VbO8REc.png)

### Defs

![Definitions](http://i.imgur.com/gePlqoU.png)

## Related materials

Here are some links to other materials related to Anki advanced configuration that helped me or inspired me somehow.

1. https://www.juliensobczak.com/tell/2016/12/26/anki-scripting.html
1. https://gist.github.com/androidfred/5562973ac1ae5ce58d305a2e81c0ebd1
1. https://github.com/nheinric/addToAnki

## Theory and methods

In this section I'd like to mention a few methods that I used in my studies, which method suited better and how I used it.

### SRS Flash Cards

The number one method is of course using Spaced Repetition Software. I only used Anki and Memrise. I am aware of Duolingo, Quizlet, and others, but I never been seriously using anything but these two. Surprisingly, Anki worked best for English, and Memrise worked best for Korean. That's personal preference, of course, you don't have to have the same usage patterns. What's important about Memrise is that it makes you type Korean words. I stongly suggest avoid the temptation of using the built-in buttons that contain whole Korean syllables. Instead -- just type using your regular keyboard, type the whole words.

In Anki, on the other hand, I do no typing checks when I study English words. I did some experiments with typing Korean in Korean decks, but it didn't go well.

This is the only high-tech method that I've used. The methods below are low-tech but it doesn't make them any worse (maybe even better).

### Method by Anastasia Kuznetsova

This method is good for remembering a bunch of words into your short-term memory. Even though the original author claims that all the words that she studied using this method she can still remember years later, I leave this statement without judgement because there is nothing in the method that trains your long-term memory. I guess the author remembered the words so well because this was just one of the tools in the language learning.

As said above, this method is good for learning words. Due to the suggested layout of the words on the paper this method isn't really good for sentenses. What you need to do is to write all your words that you'd like to remember into
a column. Take a piece of A4 paper and place it horizontally. Now write the words in foreign language in the first column. I usually write from top to bottom until I have space left.

![sample_page](https://user-images.githubusercontent.com/340676/79798983-10c71800-835a-11ea-8774-b98e04718882.jpg)

### Method by Maru Kachko

This method is good for remembering words in context or for remembering the whole sentences. It's somewhere in between in terms of short-term vs long-term memory.

It is similar to the Goldlist method below, but is less strict and formal. The idea is to write N sentenses (10 in the author's original description) every day. Drop a sentense from the list if you can easily remember it, put a new sentense to the free spot.

### Goldlist method

This method is good for remembering in long-term memory. The method is a combination of a spaced repetition and everyday writing. Basically, you write page of sentenses everyday, some of which you remember better. Those sentenses that stick in your memory best, they get filtered out and you focus on the rest next day.

Here are the relevant links that explain the method in details:

1. https://www.youtube.com/watch?v=rH6FERpM5fQ
2. https://universeofmemory.com/the-goldlist-method-scientific-critique/
3. https://howtogetfluent.com/gold-list-method/
4. https://www.open.edu/openlearn/languages/learning-languages/the-goldlist-method

## Author

(c) 2014-2020 Yuri Bochkarev
