from pymorphy2.tokenizers import simple_word_tokenize

class Symbol(object):
    """Class of marker instances
    """
    individuals = {}
    def __init__(self, name):
        """
        """
        self.name=name

    def __str__(self, ):
        """
        """
        return "<Symbol {}>".format(self.name)

    __repr__=__str__

page_symbol=Symbol("page")
paragraph_symbol=Symbol("paragraph")

class Loader(object):
    """Loads text and divides it on [paragraph] lokens.
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

    def lines(self):
        linequeue=[]
        for line in self.file:
            if line.startswith(b"\x0c"):
                line=line.lstrip(b"\x0c")

                prev=linequeue.pop()
                if prev==paragraph_symbol:  # must be an empty string
                    prev=linequeue.pop()
                    try:
                        int(prev.strip())
                    except ValueError:
                        linequeue.append(prev)
                else:
                    linequeue.append(prev)

                linequeue.append(page_symbol)

            uniline=line.decode(self.encoding)
            if uniline.strip():
                linequeue.append(uniline)
            elif linequeue[-1]!=paragraph_symbol:
                linequeue.append(paragraph_symbol)
            if len(linequeue)<10:
                continue
            yield linequeue.pop(0)

        yield from linequeue

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
