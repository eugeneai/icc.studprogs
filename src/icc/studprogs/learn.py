import icc.studprogs.popplerxml as loader
#import icc.studprogs.textloader as textloader
#import pybison
from pkg_resources import resource_stream

from itertools import islice
import sys
import pymorphy2

package=__name__
#TEST_FILE=resource_stream("icc.studprogs","data/059285.txt")
TEST_FILE=resource_stream("icc.studprogs","data/059285.xml")

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


def main(stream, limit):
    """

    Arguments:
    - `stream`: open stream to learn from
    """
    l=loader.Loader(stream)
    mt=MorphologicalTagger(l)
    for paragraph in islice(mt.paragraphs(), limit):
        for word in paragraph:
            try:
                token, attrs = word
                t=str(token)
                m=attrs["morph"]
                #t=t+"/"+str(m[0].normal_form)
                t=str(m[0].normal_form)
            except TypeError:
                t=str(word.mark)
            print (t, end=" ")
        print ()



if __name__=="__main__":
    limit = 10000
    main(TEST_FILE, limit)
    quit()
