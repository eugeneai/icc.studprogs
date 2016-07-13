#!/usr/bin/env python3
import ucto
from pkg_resources import resource_filename

settingsfile=resource_filename("icc.studprogs","etc/tokconfig-generic")

def join(lexems,
         only=[],
         filter=[],
         decor=("",""),
         with_type=False,
         no_symbols=False,
         subst={}
         ):
    """Joins sentence token into a string.

    Arguments:
    - `sent`: List or generator of tokens or tuples
                 with wirst item being a token. The result will
                 unclude str() of the token.
    - `only`: Include only tokens of type mentioned in this list.
    - `filter`: Filter out tokens of type mentioned in this list.
    - `decor`: Decorate tokens with symbols. E.g. decor=("[","]")
               produces "[<token>]".
    - `with_type`: Print each token as <token>/<token_type> is possible.
    - `no_symbols`: Remove all symbols if True.
    - `subst`: A dictionary to substitute token of a type
               to a string. Useful to substitute unwanted
               ellpsis to, e.g., dot (".", "PUNCTUATION"),.
    """
    s=[]
    only_rules=len(only)>=1
    try:
        for lexem in lexems:
            space=" "
            if type(lexem)==tuple:
                token = lexem[0]
                tt=token.type()
                if tt in filter:
                    continue
                if only_rules and not tt in only:
                    continue
                if token.nospace():
                    space=""
                t=token
                if tt in subst:
                    token,tt = subst[tt]
                else:
                    token=str(token)
                if with_type:
                    token+="/"+tt
                    if t.isendofsentence():
                        token+="<"
                    if t.isbeginofsentence():
                        token=">"+token
            else:
                if only_rules:
                   continue
                if no_symbols:
                    continue
                token=str(lexem)
            s.append(decor[0]+token+decor[1]+space)
        answer="".join(s).strip()
        return answer

    except TypeError:
        return lexems

def clean_join(sent, with_type=False, decor=("","")):
    """Joins sentence token into a string.
    It is the same as join, but some arguments
    are fixed to a reasonable values to get *clean*
    sentence.

    Arguments:
    - `sent`: List or generator of tokens or tuples
                 with wirst item being a token. The result will
                 unclude str() of the token.
    - `decor`: Decorate tokens with symbols. E.g. decor=("[","]")
               produces "[<token>]".
    - `with_type`: Print each token as <token>/<token_type> is possible.
    """
    return join(sent,
                 only=[
                     "WORD",
                     "PUNCTUATION-MULTI",
                     "PUNCTUATION",
                     #"ABBREVIATION",
                 ],
                 with_type=with_type,
                 decor=decor,
                 subst={
                     "PUNCTUATION-MULTI":(".", "PUNCTUATION"),
                 },
                 no_symbols=True
                )

class Tokenizer(object):
    """Utilization of ucto tokenizer as
    tokenizer class.
    """

    def __init__(self, textiter=None, **kwargs):
        """Initializes tokinizer. A text
        generator needed as input source.

        Arguments:
        - `textiter`: Inout source generator.
        """
        self.textiter = textiter
        #Initialise the tokeniser, options are passed as keyword arguments, defaults:
        #   lowercase=False,uppercase=False,sentenceperlineinput=False,
        #   sentenceperlineoutput=False,
        #   sentencedetection=True, paragraphdetection=True, quotedetectin=False,
        #   debug=False
        defaults={
            'lowercase':False,
            'uppercase':False,
            'sentencedetection':False,
            'paragraphdetection':False,
            'quotedetection':False,
            'sentenceperlineinput':False,
            'sentenceperlineoutput':False,
            'debug':False
            }

        defaults.update(kwargs)

        tokenizer = ucto.Tokenizer(settingsfile, **defaults)

        self.tokenizer = tokenizer

    def tokens(self):
        """Generate tokens from source text.
        """
        if self.textiter != None:
            for text in self.textiter:
                self.tokenizer.process(text)
                yield from self.tokenizer
        else:
            yield from self.tokenizer

    def sentences(self):
        """Generate sentences from source text.
        """
        if self.textiter != None:
            for text in self.textiter:
                self.tokenizer.process(text)
                yield from self.sentences()
        else:
            yield from self.sentences()

    def process(self, text):
        """Add text to further processing.
        """
        self.tokenizer.process(text)

'''
#pass the text (may be called multiple times),
tokenizer.process(text)

#we can continue with more text:
tokenizer.process("This was not enough. We want more text. More sentences are better!!!")

#there is a high-levelinterface to iterate over sentences as string, with all tokens space-separated:
for sentence in tokenizer.sentences():
    print(sentence)
'''

def test():
    text = """To be or not to be, that's the question. This is a test to tokenise. We can span
    multiple lines!!! The number 6 is Mr Li's favourite. We can't stop yet.
    This is the next paragraph. And so it ends.


        А теперь руссие идут... бутявки.
    1.1 Linux для гиков.
    1.1.2 Для продвинутых разработчиков
    1.2. Другой формат

    Технический текст <123.234>.
    <<Тест кавычек>>
    <<Тест кавычек>>
    """

    def textgen():
        for line in text.split("\n\n"):
            yield line

    print ("\n\nThe first demo, TOKEN recognition. -------")
    t = Tokenizer(textgen())

    #read the tokenised data
    for token in t.tokens():
        if token.isnewparagraph():
            print("\t", end="")
        #token is an instance of ucto.Token, serialise to string using str()
        print(  "[" + str(token) + "]", end="" )

        #tokens remember whether they are followed by a space
        if token.isendofsentence():
            print(r"\\")
        elif not token.nospace():
            print(" ",end="")

        #the type of the token (i.e. the rule that build it) is available as token.type

    print ("\n\nThe Second demo, sentence recognition. -------")

    t = Tokenizer(textgen())
    for sentence in t.sentences():
        print (sentence)

if __name__=="__main__":
    test()
    quit()
