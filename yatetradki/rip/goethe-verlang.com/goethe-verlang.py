import sys
import os
from bs4 import BeautifulSoup

#
# This script as a converted of this book into Anki cards:
# http://www.goethe-verlag.com/book2/_VOCAB/EN/ENKO/ENKO.HTM
#
# Before running, download manually all the pages of the book into the data
# directory.
#
# Then run as follows:
# python rip/goethe-verlang.com/goethe-verlang.py rip/goethe-verlang.com/data/ENKO*.HTM > korean-enko-sounds.txt
#
# URLs to sound files will be printed to stdout. You need to downloaded them
# and save into your Anki/media directory.
#
# Anki cards will be written into korean-enko.txt file.
#

# Card 1:
# English
# KoreanPartial
# ===
# English
# KoreanPartial
# ---
# KoreanPronunciation
# KoreanFull
# KoreanTranscription

# Card 2:
# KoreanPronunciation
# KoreanFull
# ===
# KoreanPronunciation
# KoreanFull
# ---
# KoreanTranscription
# English


def contains_korean(text):
    return len([(x, ord(x)) for x in text if ord(x) > 1000]) > 0


def main(filenames):
    with open('korean-enko.txt', 'w', encoding='utf8') as file_out:
        for filename in filenames:
            #filename = 'rip/goethe-verlang.com/data/ENKO061.HTM'

            with open(filename, encoding='cp1251') as file_in:
                text = file_in.read()
                soup = BeautifulSoup(text, 'lxml')
                table = soup.find_all('table')[6]
                for row in table.find_all('tr'):
                    # print(row)
                    if not contains_korean(row.text):
                        continue

                    try:
                        items = list(row.children)
                        english = items[0].text.strip('\n')
                        korean = items[1].find_all('a')
                        sound = row.find('source')['src']
                        korean_partial = korean[0].text.strip('\n ')
                        korean_full = korean[1].contents[0].strip('\n ')
                        korean_transcription = korean[1].contents[1].text.strip('\n ').replace('ndash;', '—')
                        basename = os.path.basename(sound)
                        pronunciation = '[sound:korean_enko_{0}]'.format(basename)
                        print(sound)
                        line = '\n{0}\t{1}\t{2}\t{3}\t{4}'.format(
                            english,
                            korean_full,
                            korean_partial,
                            korean_transcription,
                            pronunciation)
                        file_out.write(line)
                    except Exception as e:
                        print(e)


if __name__ == '__main__':
    main(sys.argv[1:])
