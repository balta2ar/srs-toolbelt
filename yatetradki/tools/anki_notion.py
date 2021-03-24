"""
This module contains helper script to sync toggle lists from notion
to Anki using notion2anki converter.

Usage:

    python anki_notion.py \
        --block-id 994e653dc9ef423bbc5fc9d2ddc7b4b3 \
        --anki-media '/home/bz/.local/share/Anki2/bz/collection.media' \
        --anki-sync

    OR

    srst-anki-sync-notion ...
"""

import argparse
import time
from os.path import exists, join
from pathlib import Path

import sys
sys.path.append("/usr/share/anki")

from anki import Collection
from anki.importing.apkg import AnkiPackageImporter

from yatetradki.notion2anki.notion import Notion
from yatetradki.notion2anki.notion2anki import Notion2Anki
from yatetradki.tools.anki_connect import invoke
from yatetradki.tools.anki_control import new_anki_instance
from yatetradki.tools.log import get_logger

_logger = get_logger('anki_notion')

NOTION_TMP_ZIP_FILENAME = '/tmp/notion.export.zip'
NOTION2ANKI_APKG_FILENAME = 'notion2anki.convert.apkg'
NOTION2ANKI_TMP_APKG_FILENAME = '/tmp/' + NOTION2ANKI_APKG_FILENAME


def parse_args():
    parser = argparse.ArgumentParser(description='Export Notion page with subpages')
    parser.add_argument('--block-id', type=str, required=True, help='URL to export')
    parser.add_argument('--anki-media', type=str, default='/home/bz/.local/share/Anki2/bz/collection.media',
                        help='Anki media folder to store apkg files')
    parser.add_argument('--anki-sync', default=False, action='store_true',
                        help='Sync anki to web after import')

    return parser.parse_args()


def import_collection(filename: str, full_apkg_name: str) -> None:
    assert exists(filename)
    collection = Collection(filename)
    importer = AnkiPackageImporter(col=collection, file=full_apkg_name)
    importer.run()
    time.sleep(10.0)
    _logger.info('apkg %s has been imported into anki', full_apkg_name)


def sync_anki():
    with new_anki_instance():
        invoke('sync')
        time.sleep(60.0)


def sync_from_notion(block_id: str, anki_media: str, anki_sync: bool) -> None:
    notion = Notion()
    notion.login()
    notion_blob = notion.export(block_id)
    if notion_blob.same_as(NOTION_TMP_ZIP_FILENAME):
        _logger.info('notion zip file %s is the same, skipping the rest', NOTION_TMP_ZIP_FILENAME)
        return

    apkg_blob = Notion2Anki().upload(notion_blob)
    if apkg_blob.same_as(NOTION2ANKI_TMP_APKG_FILENAME):
        _logger.info('apkg notion2anki file %s is the same, skipping the rest', NOTION2ANKI_APKG_FILENAME)
        return

    # notion_blob.save(NOTION_TMP_ZIP_FILENAME)
    # apkg_blob.save(NOTION2ANKI_TMP_APKG_FILENAME)
    # return
    # notion_blob = Blob.read(NOTION_TMP_ZIP_FILENAME)
    # apkg_blob = Blob.read(NOTION2ANKI_TMP_APKG_FILENAME)

    full_apkg_name = join(anki_media, NOTION2ANKI_APKG_FILENAME)
    apkg_blob.save(full_apkg_name)

    collection_filename = str(Path(anki_media) / '..' / 'collection.anki2')
    import_collection(collection_filename, full_apkg_name)

    notion_blob.save(NOTION_TMP_ZIP_FILENAME)
    apkg_blob.save(NOTION2ANKI_TMP_APKG_FILENAME)

    if anki_sync:
        sync_anki()


def main():
    args = parse_args()
    sync_from_notion(args.block_id, args.anki_media, args.anki_sync)


if __name__ == '__main__':
    main()
