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
            self.tree = etree.parse(self.filename)
        return self.tree

    def find_indents(self, indent_thr=0, tail_thr=0):
        """Find indents in the tree.
        """
        self.load()
        count_indents = count_tails = 0
        for line in self.tree.iterfind("//line"):
            line_bb = self.get_bbox(line, extents=True)
            page = line.getparent().getparent()
            page_bb = self.get_bbox(page, extents=True)
            # right top left bottom
            ll, pl = line_bb[0], page_bb[0]
            if ll > pl + indent_thr:
                idn = etree.Element("indent")
                idn.set("value", str(ll - pl))
                line.insert(0, idn)
                count_indents += 1
            lr, pr = line_bb[2], page_bb[2]
            if lr + tail_thr < pr:
                tail = etree.Element("tail")
                tail.set("value", str(pr - lr))
                line.append(tail)
                count_tails += 1
        return (count_indents, count_tails)

    def simple_par(self, indent_thr=20, tail_thr=20):
        """Simple paragraph recognition heuristic.
        """

        def _check(ind, tail):
            if ind is None:
                return False
            if tail is None:
                return False
            v = float(ind.get("value"))
            if v < indent_thr:
                return False
            v = float(tail.get("value"))
            if v < tail_thr:
                return False
            return True

        def _set(ind, par):
            [_.set("par", "1") for _ in [ind, par]]

        prev_ind = prev_tail = None
        count = 0
        for line in self.tree.iterfind("//line"):
            ind = line[0] if line[0].tag == "indent" else None
            tail = line[-1] if line[-1].tag == "tail" else None
            if _check(ind, tail):  # like a centered or very short par.
                _set(ind, tail)
                line.set("par-first", "1")
                line.set("par-last", "1")
                count += 1
            if _check(ind, prev_tail):
                _set(ind, prev_tail)
                line.set("par-first", "2")
                prev_tail.getparent().set("par-last", "2")
                count += 1
            prev_ind = ind
            prev_tail = tail

        prev_line = None
        for line in self.tree.iterfind("//line"):
            if line.get("par-last", "0") == "0":
                for tail in line.iterfind("tail"):
                    line.set("par-last", "4")
            if line.get("par-first", "0") == "0":
                for ind in line.iterfind("indent"):
                    line.set("par-first", "4")
            if line.get("par-first", "0") == "0":
                if prev_line is not None and prev_line.get("par-last",
                                                           "0") != "0":
                    line.set("par-first", "3")
                    ind = etree.Element("indent")
                    ind.set("value", "0")
                    line.insert(0, ind)
            prev_line = line
        return count

    def reduce_lines(self):
        def _shift(tags=None):
            for e in line.iterchildren():
                if tags is not None and e.tag not in tags:
                    continue
                line.remove(e)
                line.addprevious(e)

        for line in self.tree.iterfind("//line"):
            pf = int(line.get("par-first", "0"))
            pl = int(line.get("par-last", "0"))
            if pf == 0 and pl == 0:
                _shift(["style"])
            elif pf > 0 and pl > 0:
                _shift(["style", "indent", "tail"])
            elif pf > 0 and pl == 0:
                _shift(["style", "indent"])
            elif pf == 0 and pl > 0:
                _shift(["style", "tail"])

            line.getparent().remove(line)

    def form_par(self):
        for t in self.tree.iterfind("//text"):
            for i in t.iterfind("indent"):
                par = etree.Element("par")
                par.set("indent", i.get("value"))
                while True:
                    n = i.getnext()
                    if n is None or n.tag == "indent":
                        par.set("tail", "-1")
                        break
                    i.getparent().remove(n)
                    if n.tag == "tail":
                        par.set("tail", n.get("value"))
                        break
                    par.append(n)
                i.addprevious(par)
                i.getparent().remove(i)

    def reduce_style(self):
        for par in self.tree.iterfind("//par"):
            prev_style = None
            for style in par.iterfind("style"):
                if prev_style is not None:
                    if prev_style.attrib == style.attrib:
                        prev_style.text += style.text
                        style.getparent().remove(style)
                        continue
                prev_style = style

    def remove_pages(self, text=True):
        # Loosing the bounding boxes
        for page in self.tree.iterfind("//page"):
            number = page.get("number", None)
            for par in page.iterfind(".//par"):
                par.set("page-number", number)
            for c in page.iterchildren():
                page.remove(c)
                page.addprevious(c)
            page.getparent().remove(page)
        if text:
            for t in self.tree.iterfind("//text"):
                for c in t.iterchildren():
                    t.remove(c)
                    t.addprevious(c)
                t.getparent().remove(t)

    def get_bbox(self, tag, extents=False):
        keys = ["bbox-left", "bbox-top"]
        if extents:
            keys += ["bbox-right", "bbox-bottom"]
        else:
            keys += ["bbox-width", "bbox-height"]
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

    def write(self, filename):
        self.tree.write(
            filename,
            pretty_print=True,
            encoding="UTF-8",
            xml_declaration=True)
