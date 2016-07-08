from common import *
from lxml import html
from collections import ChainMap
import uctotokenizer as ucto

LINE_THRESHOULD=3 # px
TAB_THRESHOULD=3 # px
TAIL_THRESHOULD=10 # px

class Helper(object):
    """Helper object like JS hash.
    """
    def __str__(self):
        s=""
        for k,v in self.__dict__.items():
            if k.startswith("_"):
                continue
            s+="{}={}".format(k,v)
        return s

    __repr__=__str__

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
        self.textlines={}

    HTML_MARKUP={
        "b":(font_bold_start,font_bold_end),
        "i":(font_italic_start,font_italic_end),
        "a":(symbol_anchor_start, symbol_anchor_end),
    }

    def raw_lines(self, node=None, style=None):
        if node==None:
            self.initialize()
            style=ChainMap({"fontstyle":"n"})
            node=self.root
        for e in node.iterchildren():
            if e.tag in ["html", "body","pdf2xml"]:
                yield from self.raw_lines(e, style)
                continue
            if e.tag in ["b","i"]:
                sstart,send=self.__class__.HTML_MARKUP[e.tag]
                yield sstart
                yield from self._texts(e, style.new_child({"fontstyle": e.tag}))
                yield send
                continue
            if e.tag in ["a"]:
                sstart,send=self.__class__.HTML_MARKUP[e.tag]
                yield sstart
                yield from self._texts(e, style)
                yield send
                continue
            if e.tag=="page":
                yield from self._proc_page(e, style)
                yield page_symbol
                continue
            #if e.tag == "text":
            #    yield from self._proc_text(e, style)
            #    continue
            yield e
            yield from self.raw_lines(e,style)

    def raw_lexems(self):
        tokenizer=ucto.Tokenizer()
        for lors in self.raw_lines():
            if type(lors)!=tuple:
                yield lors
                continue
            phrase, style = lors
            tokenizer.process(phrase)
            for token in tokenizer.tokens():
                yield token, style

    def _proc_fontspec(self, e):
        a = self.attrib(e)
        self.fontspec[a.get("id")]=a

    def _texts(self, e, style):
        def _text(t, style):
            if not type(t)==type(""):
                return
            if type(t)==type(b""):
                t=t.decode(self.encoding)
            yield t, style
        style = style.new_child({"element":e})
        yield from _text(e.text,style)
        yield from self.raw_lines(e,style)
        yield from _text(e.tail,style)

    def _proc_text(self, e, style):
        """Process text element

        Arguments:
        - `e`: Node to be processed
        <text top="110" left="489" width="5" height="16" font="0"><b> </b></text>
        """
        a = self.attrib(e)
        l,t,w,h=self.get(a, "left", "top", "width", "height")
        r,b=l+w,t+h
        pl,pt,pw,ph=self.get(self.page, "eleft", "etop", "ewidth", "eheight")
        pr,pb=pl+pw,pt+ph
        if r<pl or l>pr or b<pt or t>pb:
            return
        font = a.get("font")
        style = style.new_child({"fontspec":self.fontspec[font],"text":e}).new_child(a)
        yield from self._texts(e, style)

    def texts_of_page(self, e):
        """Iterate over text blocks except
        printed page number.
        """
        pn=self.page["number"]
        for text in e.iterchildren(tag="text"):
            tt=text.text
            if tt !=None:
                if tt.strip()==str(pn):
                    continue
            yield text

    def _proc_page(self, epage, style=None):
        self.page=self.attrib(epage)

        for fontspec in epage.iterchildren(tag="fontspec"):
            self._proc_fontspec(fontspec)

        ext=Helper()
        inf=1e10
        ext.x=ext.y=inf
        ext.h=ext.w=-inf
        texts=set()
        for text in self.texts_of_page(epage):
            ta=self.attrib(text)
            texts.add(text)
            x,y,w,h=self.get(ta, "left", "top", "width", "height")
            w+=x
            h+=y
            if ext.x>x: ext.x=x
            if ext.y>y: ext.y=y
            if ext.w<w: ext.w=w
            if ext.h<h: ext.h=h

        self.page.update({"eleft":ext.x, "etop":ext.y, "ewidth":ext.w-ext.x, "eheight":ext.h-ext.y})
        tl=self.textlines={}
        for text in self.texts_of_page(epage):
            ta=self.attrib(text)
            l,t,w,h=self.get(ta, "left", "top", "width", "height")
            b=t+h
            r=l+w
            found=False
            for btl,ld in tl.items():
                ttl=ld.t
                if b>=ttl and abs(b-btl) < LINE_THRESHOULD:
                    found=True
                    break
                #if t>=ttl and t<=btl:
                #    found=True
                #    break
            if found:
                if ld.b<b: ld.b=b
                if ld.t>t: ld.t=t
            else:
                ld=tl[b]=Helper()
                ld.b,ld.t=b,t
                ld.li=[]
            ld.li.append(text)
        for lb in tl.values():
            lb.li.sort(key=lambda text: int(text.get("left")))
            lb.l=int(lb.li[0].get("left"))
            bl=lb.li[-1]
            bli=int(bl.get("left"))
            blw=int(bl.get("width"))
            lb.w=bli-lb.l+blw

        lines=list(tl.keys())
        lines.sort()
        for line in lines:
            yield line_start
            lb=tl[line]
            li=lb.li
            pl=self.page.get("eleft")
            pr=pl+self.page.get("ewidth")
            if abs(pl-lb.l)>TAB_THRESHOULD:
                yield line_tab
            for text in lb.li:
                yield from self._proc_text(text, style)
            if abs(pr-(lb.l+lb.w))>TAIL_THRESHOULD:
                yield line_tail
            yield line_end

    def lexems(self):
        """Generates lexems in a "standart" form.
        """
        paragraph_started=False
        for lexem in self.raw_lexems():
            if lexem in [line_start, line_end]:
                continue
            if lexem == line_tail:
                if paragraph_started:
                    yield paragraph_symbol
                    paragraph_started = False
                continue

            if lexem == line_tab:
                if paragraph_started:
                    yield paragraph_symbol
                    paragraph_started = True
                continue
            if lexem == page_symbol:
                continue
            paragraph_started = True
            yield lexem


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

    def get(self, d, *keys):
        """
        Return tuple of values from the dictionary.
        Arguments:
        - `d`: The dictionary to take values from;
        - `*keys`: values.
        """
        rc=[]
        for k in keys:
            rc.append(d[k])
        return rc


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

    def just_lex(l):
        if type(l) == tuple:
            token=l[0]
            #token is an instance of ucto.Token, serialise to string using str()
            s="[" + str(token) + "]"
            end=""
            if token.isnewparagraph():
                s="\t"+s

            #tokens remember whether they are followed by a space
            if token.isendofsentence():
                end=r"\\"
            elif not token.nospace():
                end=" "
            return s, end

        else:
            return (l.mark, " ")

    for par in _iterator(loader.paragraphs(),limit):
        lexems=(just_lex(l) for l in par)
        for lexem, end in lexems:
            print (lexem, end=end)
        print ("\n")
        continue
        print (lexem, end=" ")
        for k,v in style.items():
            print ("{}={}".format(k,v), end=",")
        print ()
    print ("Collected fontspecs:")
    pprint.pprint(loader.fontspec)


if __name__=="__main__":
    #test()
    test(limit=10000)
    quit()
