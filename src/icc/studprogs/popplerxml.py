from common import *
from lxml import html
from collections import ChainMap

class Helper(object):
    """Helper object like JS hash.
    """
    def __str__(self):
        s=""
        for k,v in self.__dict__:
            if k.startswith("_"):
                continue
            s+="{}={}".format(k,v)
        return s

class Loader(BaseLoader):
    """Loads poppler xml, translates it via iterators.
    """

    def initialize(self):
        """Initializes internal structures.
        """
        self.fontspec={}
        self.tree=None
        self.styles=ChainMap({"font_style":"normal"})
        self.tree=html.parse(self.file)
        self.root=self.tree.getroot()
        self.page={}

    def lexems(self, node=None, style=None):
        if node==None:
            self.initialize()
            style=ChainMap({"fontstyle":"n"})
            node=self.root
        for e in node.iterchildren():
            if e.tag in ["html", "body","pdf2xml"]:
                yield from self.lexems(e, style)
                continue
            if e.tag in ["b","i"]:
                yield from self._texts(e, style.new_child({"fontstyle": e.tag}))
                continue
            if e.tag in ["a"]:
                yield from self._texts(e, style)
                continue
            if e.tag=="page":
                self._proc_page(e,style)
                yield from self.lexems(e, style)
                yield page_symbol
                continue
            if e.tag == "fontspec":
                self._proc_fontspec(e)
                yield from self.lexems(e, style)
                continue
            if e.tag == "text":
                yield from self._proc_text(e, style)
                continue
            yield e
            yield from self.lexems(e,style)

    def _proc_fontspec(self, e):
        a = self.attrib(e)
        self.fontspec[a.get("id")]=a

    def _proc_text(self, e, style):
        """Process text element

        Arguments:
        - `e`: Node to be processed
        <text top="110" left="489" width="5" height="16" font="0"><b> </b></text>
        """
        a = self.attrib(e)
        font = a.get("font")
        style = style.new_child({"fontspec":self.fontspec[font],"text":e}).new_child(a)
        yield from self._texts(e, style)

    def _proc_page(self, e, style=None):
        self.page=self.attrib(e)
        pn=self.page["number"]
        ext=Helper()
        inf=1e10
        ext.x=ext.y=inf
        ext.h=ext.w=-inf
        for text in e.iterchildren(tag="text"):
            ta=self.attrib(text)
            tt=text.text
            if tt !=None:
                if tt.strip()==str(pn):
                    continue
            x,y,w,h=ta["left"],ta["top"],ta["width"],ta["height"]
            w+=x
            h+=y
            if ext.x>x: ext.x=x
            if ext.y>y: ext.y=y
            if ext.w<w: ext.w=w
            if ext.h<h: ext.h=h
            #print("--->", text.tag, text.attrib, text.text, text.tail)
        self.page.update({"eleft":ext.x, "etop":ext.y, "ewidth":ext.w, "eheight":ext.h})
        print ("--->", self.page)

    def _texts(self, e, style):
        def _text(t, style):
            if not type(t)==type(""):
                return
            if type(t)==type(b""):
                t=t.decode(self.encoding)
            for token in simple_word_tokenize(t):
                yield token, style
        style = style.new_child({"element":e})
        yield from _text(e.text,style)
        yield from self.lexems(e,style)
        yield from _text(e.tail,style)

    def attrib(self, e):
        """Return attrib dictionary with
        values coverted to numbers if
        possible.
        """
        attrib = e.attrib
        n={}
        for k,v in attrib.items():
            try:
                v=int(v)
                n[k]=v
                continue
            except ValueError:
                pass
            try:
                v=float(v)
                n[k]=v
                continue
            except ValueError:
                pass
            n[k]=v
        return n

def test(limit=100):
    from pkg_resources import resource_stream
    from itertools import islice
    import pprint
    TEST_FILE=resource_stream("icc.studprogs","data/059285.xml")
    loader=Loader(TEST_FILE)

    def _iterator(initer, limit):
        if limit==0:
            return initer
        return islice(initer, limit)

    for lexem in _iterator(loader.lexems(),limit):
        if type(lexem) == tuple:
            lexem,style = lexem
        else:
            style = {}
        print (lexem, end=" ")
        for k,v in style.items():
            print ("{}={}".format(k,v), end=",")
        print ()
    # pprint.pprint(loader.fontspec)


if __name__=="__main__":
    test()
    quit()
