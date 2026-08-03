#!/usr/bin/env python3

"""
Standalone command to sync the local Anki collection with AnkiWeb.

It reads credentials from environment variables:

    ANKIWEB_USER
    ANKIWEB_PASSWORD

If these are not set in the environment, they are read automatically from
~/.anki (or the file pointed to by the ANKI_ENV_FILE environment variable),
which is a simple KEY=VALUE file, e.g.:

    ANKIWEB_USER=you@example.com
    ANKIWEB_PASSWORD=secret

Real environment variables always take precedence over values from the file.

The collection path defaults to the usual Anki2 location but can be overridden
with the ANKI_COLLECTION environment variable or the --collection argument.

Usage:

    srst-anki-sync
    srst-anki-sync --collection /path/to/collection.anki2
    ANKIWEB_USER=... ANKIWEB_PASSWORD=... srst-anki-sync
"""

import argparse
import os
from os.path import expanduser, expandvars, isfile

from anki.collection import Collection

from yatetradki.tools.log import get_logger

_logger = get_logger('anki_sync_web')


DEFAULT_ENV_FILE = '~/.anki'
DEFAULT_COLLECTION = '/home/bz/.local/share/Anki2/bz/collection.anki2'


def load_env_file(path):
    """Load KEY=VALUE pairs from path into a dict (does not touch os.environ)."""
    values = {}
    if not path:
        return values
    path = expanduser(expandvars(path))
    if not isfile(path):
        _logger.debug('Env file not found: %s', path)
        return values
    _logger.debug('Reading env file: %s', path)
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve(name, file_values, override=None):
    """Real env var wins, then explicit override, then the env file."""
    if os.getenv(name):
        return os.getenv(name)
    if override:
        return override
    return file_values.get(name)


def web_sync(collection, user, password):
    if not user or not password:
        raise SystemExit(
            'Missing AnkiWeb credentials. Set ANKIWEB_USER and '
            'ANKIWEB_PASSWORD in the environment or in the env file '
            '(default ~/.anki).')
    _logger.info('Opening collection: %s', collection)
    col = Collection(collection)
    try:
        _logger.info('Logging in to AnkiWeb as %s', user)
        auth = col.sync_login(user, password, None)
        _logger.info('Syncing collection (with media)...')
        col.sync_collection(auth, sync_media=True)
        _logger.info('Sync finished.')
    finally:
        col.close()


def main():
    parser = argparse.ArgumentParser(description='Sync local Anki collection with AnkiWeb.')
    parser.add_argument('--env-file', default=os.getenv('ANKI_ENV_FILE', DEFAULT_ENV_FILE),
                        help='Path to KEY=VALUE env file (default: ~/.anki).')
    parser.add_argument('--collection', default=os.getenv('ANKI_COLLECTION', DEFAULT_COLLECTION),
                        help='Path to the collection.anki2 file.')
    parser.add_argument('--user', default=None, help='AnkiWeb user (overrides env file).')
    parser.add_argument('--password', default=None, help='AnkiWeb password (overrides env file).')
    args = parser.parse_args()

    file_values = load_env_file(args.env_file)
    user = resolve('ANKIWEB_USER', file_values, args.user)
    password = resolve('ANKIWEB_PASSWORD', file_values, args.password)

    web_sync(args.collection, user, password)


if __name__ == '__main__':
    main()
