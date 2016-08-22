from nose.tools import *
import nose
import icc.studprogs.textloader as loader
import icc.studprogs.uctotokenizer as ucto
from icc.studprogs.common import Symbol
from pkg_resources import resource_stream

from itertools import islice, cycle

#TEST_FILE1=resource_stream("icc.studprogs","data/059285.txt")
#TEST_FILE2=resource_stream("icc.studprogs","data/059285.xml")
#TEST_FILE3=resource_stream("icc.studprogs","data/grin.txt")

class Tests:
    def setUp(self):
        self.stream=resource_stream("icc.studprogs","data/grin.txt")
        self.l=loader.Loader(self.stream)

    def tearDown(self):
        del self.l
        del self.stream

    def test_loading_10_sentences(self):
        num=0
        for sent in islice(self.l.sentences(),10):
            num+=1
            if type(sent)==Symbol:
                print (sent)
            else:
                print (" ".join([str((str(t[0]), t[0].isendofsentence())) for t in sent]))
        assert num==10

    def test_printing_10_sentences(self):
        for sent in islice(self.l.sentences(),10):
            if not type(sent)==Symbol:
                s=ucto.join(sent)
                print (s)
                assert type(s)==str

    def test_printing_10_sentences_with_decor(self):
        for sent in islice(self.l.sentences(),10):
            if not type(sent)==Symbol:
                s=ucto.join(sent, decor="[]")
                print (s)
                s=s.strip()
                for t in s.split():
                    assert t[0]=='[' and t[-1]==']'

def run(test_name):
    t=Tests()
    t.setUp()
    getattr(t, test_name)()
    t.tearDown()



if __name__=="__main__":
    #result = nose.run()
    run("test_printing_10_sentences_with_decor")
    quit()
