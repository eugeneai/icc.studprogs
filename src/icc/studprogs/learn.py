import icc.studprogs.popplerxml as loader
import icc.studprogs.textloader as textloader
#import pybison
from pkg_resources import resource_stream

from itertools import islice, cycle
import sys
import pymorphy2

import icc.linkgrammar as lg

package=__name__
TEST_FILE1=resource_stream("icc.studprogs","data/059285.txt")
TEST_FILE2=resource_stream("icc.studprogs","data/059285.xml")
TEST_FILE3="./grin.txt"

class MorphologicalTagger(object):
    """Tag a lexems in a stream morphoogically
    by means of pymorphy2.
    """

    def __init__(self, lexemiterator):
        """Initialize class with
        lexem iterator source
        """
        self.lexemiterator=lexemiterator
        self.analyzer=None

    def paragraphs(self):
        """Tag each token morphologically
        and construct paragraph again. # FIXME Write it more clear.
        """
        self.analyzer = pymorphy2.MorphAnalyzer()
        for paragraph in self.lexemiterator.paragraphs():
            yield self._tag(paragraph)

    def _tag(self, par):
        new_par=[]
        for lexeme in par:
            if type(lexeme)==tuple:
                token, attrs = lexeme
                tok=str(token)
                rc=self.analyzer.parse(tok)
                new_par.append((token,attrs.new_child({"morph":rc})))
            else:
                new_par.append(lexeme)
        return new_par

class LinkGrammar(object):
    """
    """

    def __init__(self, paragraphiterator, lang="ru", only_valid=True):
        """Initialize class with
        paragraph iterator source
        """
        self.paragraphiterator=paragraphiterator
        self.lg=lg.LinkGrammar(lang)
        self.make_options()
        self.lang=lang
        self.analyzer=None
        self._maxlinkages=1
        self._linkages=self._maxlinkages
        self.only_valid=only_valid

    def make_options(self):
        self.lg.linkage_limit=1000
        self.lg.max_parse_time=10
        self.lg.verbosity=100
        pass
        # self.options=lg.ParseOptions(linkage_limit=1,
        #                              verbosity=0,
        #                              islands_ok=True,
        #                              max_parse_time=10)

    def linkages(self, text):
        """Analyses one sentence.

        Arguments:
        - `text`: Input sentence.
        """
        #dictionary=lg.Dictionary(self.lang)
        #self.make_options()
        self.lg.parse(text)
        #rc = sent.split()
        #if rc < 0:
        #    print ("--- Cannot split ---")
        #    del sent
        #    return iter(())

        print ("V:", self.lg.num_valid, "L:", self.lg.num_linkages)
        print (repr(text))
        if self.only_valid:
            for i in range(min(self.lg.num_valid, self._maxlinkages)):
                yield True, self.lg.diagram()
                #yield True, "11111"
        else:
            v=self.lg.num_valid
            for i in range(min(self.lg.num_linkages, self._maxlinkages)):
                yield i<=v, self.lg.diagram()
                #yield i<=v, "22222"

    def paragraphs(self, verbose=0):
        for par in self.paragraphiterator:
            par=par.strip()
            if not par:
                continue
            if verbose:
                print ("PAR:", repr(par))

            anylink=False
            for rc, linkage in self.linkages(par):
                if verbose:
                    if rc:
                        print ("----SUCCEED------")
                    else:
                        print ("----FAILED------")
                yield par, rc, linkage

def _print(par, rc, linkage):
    """
    """

    print ("PAR:",par)
    if linkage:
        print (rc, linkage)
        if not rc:
            print ("MSG:!!")
    else:
        print ("---NO LINKAGE---")


def link_parsing1(stream, loader_class, limits):
    l=loader_class(stream)
    linkgram=LinkGrammar(l.paragraphs(join=True, style="hidden",
                                                    only_words=False),
                         only_valid=False)
    linkgram=islice(linkgram.paragraphs(verbose=0), limit)
    for par, rc, linkage in linkgram:
        _print(par, rc, linkage)

def link_parsing11(stream, loader_class, limits):
    l=loader_class(stream)
    for par in l.paragraphs(join=True, style="hidden", only_words=False):
        print (par)

def link_parsing2(_1,_2,limits):
    sent1='''Производственная практика проводится в структурных
    подразделениях ИРНИТУ или других организациях.
    Для выполнения заданий самостоятельной работы по производственной
    практике вуз обеспечивает свободный доступ к библиотечным фондам,
    к сети Интернет и базам данных вуза и кафедры.'''
    sent2='''Богатство заключается в многообразии потребностей и желаний.'''
    sent3="Итогом преддипломной практики является выпускная квалификационная работа ."
    linkgram=LinkGrammar([sent3,sent1,sent2], only_valid=False)
    linkgram=islice(linkgram.paragraphs(verbose=0), limit)

    for par, rc, linkage in linkgram:
        _print(par, rc, linkage)


def main(stream, loader_class, limit):
    """

    Arguments:
    - `stream`: open stream to learn from
    """
    l=loader_class(stream)
    mt=MorphologicalTagger(l)
    for paragraph in islice(mt.paragraphs(), limit):
        for word in paragraph:
            try:
                token, attrs = word
                t=str(token)
                m=attrs["morph"]
                t=t
                ## t=t+"/"+str(m[0].normal_form)
                ## t=str(m[0].normal_form)
            except TypeError:
                t=str(word.mark())
            print (t, end=" ")
        print ("\n"+"-"*20)

def debug_reverse(iterator):
    r=reversed(list(iterator))
    yield from r

if __name__=="__main__":
    limit = 10
    # main(TEST_FILE1, limit)
    # link_parsing1(TEST_FILE2, loader.Loader, limit)
    link_parsing1(TEST_FILE3, textloader.Loader, limit)
    quit()
