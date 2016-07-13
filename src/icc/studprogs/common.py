import icc.studprogs.uctotokenizer as ucto

class Symbol(object):
    """Class of marker instances
    """
    individuals = {}
    def __init__(self, name, mark=None, nospace=False, **kwargs):
        """
        """
        self.name=name
        self._mark=mark
        self._nospace=nospace
        for k, v in kwargs.items():
            setattr(self, k,v)

    def __str__(self, ):
        """
        """
        return "<Symbol {}>".format(self.name)

    __repr__=__str__

    def nospace(self):
        return self._nospace()

    def mark(self, style=None):
        """Print it in a markdown like mode.
        """
        if style=="hidden":
            return ""
        if style in [None, "shown"]:
            if self._mark != None:
                return self._mark
            else:
                return str(self)

page_symbol=Symbol("page",r"\newpage"+"\n", nospace=True)
paragraph_symbol=Symbol("paragraph", r"\par"+"\n", nospace=True)
line_tab=Symbol("line tab", r"-->", nospace=True)
line_tail=Symbol("line tail", r"<--", nospace=True)
line_start=Symbol("line start", "", nospace=True)
line_end=Symbol("line end", "\n", nospace=True)
sentence_end=Symbol("sentence end", "\n", nospace=True)
symbol_anchor_start=Symbol("anchor", "<", nospace=True)
symbol_anchor_end=Symbol("anchor", ">", nospace=False)
font_bold_start = Symbol("start bold", "**", nospace=True)
font_bold_end = Symbol("end bold", "**", nospace=False)
font_italic_start = Symbol("start italic", "*", nospace=True)
font_italic_end = Symbol("end italic", "*", nospace=False)

class BaseLoader(object):
    """Implements basic loader functions.
    """

    def __init__(self, file=None, encoding="utf-8", **kwargs):
        """

        Arguments:
        - `file`: string filename or open [binary] file to be loaded.
        - `encoding`: encoding of input text defaults to utf-8.
        """
        if type(file)==type(""):
            file=open(file,"rb")
        self.file = file
        self.encoding = encoding
        self.options = kwargs
        # Options are not checked and defined as follows:
        # line_paragraph - Each line is a paragraph.
        # enpty_line_paragraph - Paragraphs recognized
        #                  as empty lines, i.e. "\n\n".
        self.options.setdefault("line_paragraph", True)
        self.options.setdefault("empty_line_paragraph", False)

    def initialize(self):
        """Initializes internal structures of
        a descendant loader.
        """
        pass

    def lines(self):
        """Generates lines and page/paragraph events
        """
        self.initialize()
        raise RuntimeError("Implemented by a subclass")

    def sentences(self):
        sent = []
        for lexem in self.lexems():
            if type(lexem) == Symbol:
                if lexem == sentence_end and sent:
                    yield sent
                    sent = []
                else:
                    yield lexem

    def paragraphs(self,
                   pages_are_paragraphs = True,
                   join=False,
                   style=None,
                   decorations=("",""),
                   only_words=False,
                   by_sentences=False
    ):
        if join:
            for par in self.paragraphs(pages_are_paragraphs = pages_are_paragraphs,
                                join=False):
                npar = []
                for lexem in par:
                    space=" "
                    if type(lexem) == tuple:
                        token, _style = lexem
                        try:
                            tok_type=token.type()
                        except AttributeError:
                            tok_type="WORD"
                        if only_words:
                            if not tok_type in ["WORD", "PUNCTUATION-MULTI", "PUNCTUATION"]:
                                continue
                            if tok_type in ["PUNCTUATION-MULTI"]:
                                #space=""
                                token="."
                            t9=str(token)
                            if tok_type == "WORD" and not t9.isalpha():
                                continue
                    else:
                        token = lexem.mark(style=style)
                        #if not token:
                            #space=""
                    #if hasattr(token, "nospace") and token.nospace():
                        #space=""
                    npar.append(decorations[0]+str(token)+decorations[1]+space)
                yield "".join(npar)
            return
        # Generate paragraph as list of lexems
        paragraph = []
        for lexem in self.lexems():
            if lexem == paragraph_symbol:
                if paragraph:
                    yield paragraph
                paragraph = []
                continue
            if lexem == page_symbol:
                if pages_are_paragraphs:
                    if paragraph:
                        yield paragraph
                    paragraph = []
                continue
            paragraph.append(lexem)
        if paragraph:
            yield paragraph

    def lexems(self):
        tokenizer=ucto.Tokenizer()
        prev=None
        for line in self.lines():
            if type(line)==type(""):
                any_tok=False
                tokenizer.process(line)
                for token in tokenizer.tokens():
                    prev = token
                    any_tok = True
                    yield token, {}
                    if token.isendofsentence():
                        yield sentence_end
                    #if token.isnewparagraph():
                    #    pass
                if self.options["line_paragraph"]:
                    yield paragraph_symbol

                if self.options["empty_line_paragraph"] and not any_tok:
                    yield paragraph_symbol
            else:
                prev = line
                yield line
        if prev == paragraph_symbol:
            yield page_symbol
            return
        if prev == paragraph_symbol:
            return
        yield paragraph_symbol
        yield page_symbol
