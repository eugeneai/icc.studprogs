from common import *
from lxml import html
from collections import ChainMap


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
        self.fontspec[e.get("id")]=e.attrib

    def _proc_text(self, e, style):
        """Process text element

        Arguments:
        - `e`: Node to be processed
        <text top="110" left="489" width="5" height="16" font="0"><b> </b></text>
        """
        font = e.get("font")
        style = style.new_child({"font":self.fontspec[font],"text":e}).new_child(e.attrib)
        yield from self._texts(e, style)

    def _texts(self, e, style):
        def _text(t, style, pos):
            if not type(t)==type(""):
                return
            if type(t)==type(b""):
                t=t.decode(self.encoding)
            d={}
            style = style.new_child(d)
            for token in simple_word_tokenize(t):
                d["pos"]=pos
                pos += 1
                yield token, style, pos
        style = style.new_child({"element":e})
        yield from _text(e.text,style,0)
        yield self.lexems(e,style)
        yield from _text(e.tail,style)

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
