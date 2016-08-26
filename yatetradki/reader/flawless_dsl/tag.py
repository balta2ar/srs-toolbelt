# -*- coding: utf-8 -*-
# flawless_dsl/tag.py
#
""" internal stuff.  Tag class"""
#
# Copyright (C) 2016 Ratijas <ratijas.t@me.com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.


from collections import namedtuple


Tag = namedtuple('Tag', ['opening', 'closing'])

def __repr__(self):
    if self.opening == self.closing:
        return 'Tag(%r)' % self.opening
    return 'Tag(%r, %r)' % self

Tag.__repr__ = __repr__
del __repr__

def was_opened(stack, tag):
    """
    check if tag was opened at some layer before.

    :param stack: Iterable[layer.Layer]
    :param tag: tag.Tag
    :return: bool
    """
    if not len(stack):
        return False
    layer = stack[-1]
    if tag in layer:
        return True
    return was_opened(stack[:-1], tag)


predefined = ['m', '*', 'ex', 'i', 'c']

def canonical_order(tags):
    """
    arrange tags in canonical way, where (outermost to innermost):
    m  >  *  >  ex  >  i  >  c
    with all other tags follow them in alphabetical order.

    :param tags: Iterable[Tag]
    :return: List
    """
    result = []
    tags = list(tags)
    for predef in predefined:
        t = next((t for t in tags if t.closing == predef), None)
        if t:
            result.append(t)
            tags.remove(t)
    result.extend(sorted(tags, key=lambda x: x.opening))
    return result


def index_of_layer_containing_tag(stack, tag):
    """
    return zero based index of layer with `tag` or None

    :param stack: Iterable[layer.Layer]
    :param tag: str
    :return: int | None
    """
    for i, layer in enumerate(reversed(stack)):
        for t in layer.tags:
            if t.closing == tag:
                return len(stack) - i - 1
    return None
