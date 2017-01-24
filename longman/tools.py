from __future__ import print_function
import os
import sys
import errno


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
