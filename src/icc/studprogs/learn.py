import icc.studprogs.popplerxml as loader
#import icc.studprogs.textloader as textloader
#import pybison
from pkg_resources import resource_stream

from itertools import islice
import sys
import pymorphy2

import linkgrammar as lg

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

class LinkGrammar(object):
    """
    """

    def __init__(self, paragraphiterator, lang="ru"):
        """Initialize class with
        paragraph iterator source
        """
        self.paragraphiterator=paragraphiterator
        self.options=lg.ParseOptions(linkage_limit=1,
                                     verbosity=1,
                                     islands_ok=True,
                                     max_parse_time=5)
        self.lang=lang
        self.dictionary=lg.Dictionary(self.lang)
        self.analyzer=None

    def linkages(self, text):
        """Analyses one sentence.

        Arguments:
        - `text`: Input sentence.
        """
        #dictionary=lg.Dictionary(self.lang)
        dictionary=self.dictionary
        sent=lg.Sentence(text, dictionary, self.options)
        return sent.parse()

    def paragraphs(self):
        yield from self.paragraphiterator

def link_parsing(stream, limit):
    """

    Arguments:
    - `stream`: open stream to learn from
    """
    l=loader.Loader(stream)
    linkgram=LinkGrammar(islice(l.paragraphs(join=True, style="hidden", only_words=True), limit))
    answer=[]
    prev=""
    for par in linkgram.paragraphs():
        sticked=False
        done=False
        par=par.strip()
        if not par:
            continue
        # if len(par)>280:
        #     print ("Skip")
        #     continue
        tries=2
        bad=[]

        while tries>0:
            print ("PARSING:", repr(par))
            for linkage in linkgram.linkages(par):
                print (linkage.diagram())
                prev=par
                done=True
                if sticked:
                    answer.pop()
                answer.append((True,par))
                break
            else:
                print ("----FAILED------")
                bad.append(par)
                par=prev+" "+par
                sticked=True
            if done:
                break  # from a while True cycle
            tries-=1
            if tries==0:
                par=bad.pop(0)
                prev=par
                answer.append((False, par))
    return answer


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
                t=t
                ## t=t+"/"+str(m[0].normal_form)
                ## t=str(m[0].normal_form)
            except TypeError:
                t=str(word.mark())
            print (t, end=" ")
        print ("\n"+"-"*20)



if __name__=="__main__":
    limit = 1000000
    main(TEST_FILE, limit)
    if 0:
         rc=link_parsing(TEST_FILE, limit)
         for a,t in rc:
             if a:
                 a="+"
             else:
                 a="-"
             print (a, t)
    quit()
