from lxml import etree

from itertools import islice, cycle
import sys
import pymorphy2

import icc.linkgrammar as lg
import icc.studprogs.uctotokenizer as ucto
from icc.studprogs.common import paragraph_symbol, Symbol

import locale
locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")


class XMLProcessor(object):
    """Process class XML loaded in order to
    find paragraphs there.
    All manipulations made in-place.
    """

    def __init__(self, filename):
        """
        parameters:
        `filename` is a filename of XML to load.
        """
        self.filename = filename
        self.tree = None

    def load(self):
        if self.tree is None:
            print (self.filename)
            self.tree = etree.parse(self.filename)
        return self.tree

    def find_indents(self):
        """Find indents in the tree.
        """

        for page in self.iterfind("page"):
            pbb = self.get_bbox(page)
            print("Page bbox", bbb)

    def get_bbox(self, tag):
        keys = ["bbox-left", "bbox-top", "bbox-width", "bbox-height"]
        return self.get_values(tag, keys)

    def get_values(self, tag, keylist):
        def _pproc(x):
            try:
                return int(x)
            except ValueError:
                pass
            try:
                return float(x)
            except ValueError:
                return x

        vals = [_pproc(tag.get(k)) for k in keylist]
        return vals
