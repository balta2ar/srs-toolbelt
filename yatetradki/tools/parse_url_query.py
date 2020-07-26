"""
Usage:

$ echo "https://enno.dict.cc/?s=en+gang&failed_kw=engang" | parse_url_query.py "s"
en gang
"""
from sys import argv, stdin, stdout
from os.path import basename
from urllib.parse import parse_qs, urlparse


def main():
    for line in stdin.readlines():
        line = line.strip()
        if not line:
            continue
        parsed_url = urlparse(line)
        if argv[1] == 'param':
            try:
                result = "".join(parse_qs(parsed_url.query)[argv[2]]).strip()
            except KeyError:
                result = None
        elif argv[1] == 'query_basename':
            result = basename(parsed_url.path).strip()
        if result:
            print(result)
            stdout.flush()


if __name__ == '__main__':
    main()
