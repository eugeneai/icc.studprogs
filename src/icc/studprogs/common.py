from pymorphy2.tokenizers import simple_word_tokenize

class Symbol(object):
    """Class of marker instances
    """
    individuals = {}
    def __init__(self, name, mark=None):
        """
        """
        self.name=name
        self._mark=mark

    def __str__(self, ):
        """
        """
        return "<Symbol {}>".format(self.name)

    __repr__=__str__

    @property
    def mark(self):
        """Print it in a markdown like mode.
        """
        if self._mark != None:
            return self._mark
        else:
            return str(self)


page_symbol=Symbol("page",r"\newpage"+"\n")
paragraph_symbol=Symbol("paragraph", r"\par"+"\n")
line_tab=Symbol("line tab", r"-->")
line_tail=Symbol("line tail", r"<--")
line_start=Symbol("line start", "")
line_end=Symbol("line end", "\n")

class BaseLoader(object):
    """Implements basic loader functions.
    """

    def __init__(self, file=None, encoding="utf-8"):
        """

        Arguments:
        - `file`: string filename or open [binary] file to be loaded.
        - `encoding`: encoding of input text defaults to utf-8.
        """
        if type(file)==type(""):
            file=open(file,"rb")
        self.file = file
        self.encoding = encoding

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
        pass

    def paragraphs(self, pages_are_paragraphs = True):
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
        prev=None
        for line in self.lines():
            if type(line)==type(""):
                for token in simple_word_tokenize(line):
                    prev = token
                    yield token
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
