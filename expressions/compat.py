# -*- encoding: utf-8 -*-
"""Python compatibility utilities"""

from __future__ import absolute_import

import sys

py3k = sys.version_info >= (3, 0)

if py3k:
    string_type = str
    text_type = str

    def unicode_escape(s):
        return bytes(s, "utf-8").decode("unicode_escape")

else:
    string_type = basestring
    text_type = unicode

    def unicode_escape(s):
         return s.decode("string-escape")

