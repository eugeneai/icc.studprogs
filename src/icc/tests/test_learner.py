from nose.tools import raises, nottest
from pkg_resources import resource_filename
from icc.studprogs.learn import XMLTextPropertyExtractor
#from icc.studprogs.importer import msdocx
from icc.studprogs.importer import tdfodt
from lxml import etree
from nose.plugins.skip import SkipTest
from glob import glob
import os.path
import pprint
from hashlib import sha1

LONG_DOCS = True
LONG_COUNT = 20
LONG_REPLACE = True

package = __name__
DATA_DIR = resource_filename("icc.studprogs", "data/annotations/")
DOC_DIR = os.path.join(DATA_DIR, "documents")
EXT_PATTERN = "*.odt"
DOC_EXT_PATTERN = "**/"+EXT_PATTERN
LEARN_PATTERN = "*-learn.xml"

FILES = glob(os.path.join(DATA_DIR, EXT_PATTERN))
if LONG_DOCS:
    g = os.path.join(DOC_DIR, DOC_EXT_PATTERN)
    DOCS = glob(g, recursive=True)
    #print (DOCS)
    #print ("glob:", g)

LEARN_FILES = glob(os.path.join(DATA_DIR, LEARN_PATTERN))

def absoluteFilePaths(directory):
   for dirpath,_,filenames in os.walk(directory):
       for f in filenames:
           yield os.path.abspath(os.path.join(dirpath, f))

class TestBasicLoad:
    def setUp(self):
        pprint.pprint(FILES)
        fl=[f for f in FILES if f.endswith('15.03.01_WP_IRA_FGOS_PLUS.odt')]
        docname = self.docname = fl[0]
        self.output_filename = \
            self.docname.replace("annotations","out").replace(".odt",".xml")
        self.e = XMLTextPropertyExtractor(
            filename=docname, importer=tdfodt.Importer)

    def tearDown(self):
        pass

    def test_extract_basic(self):
        self.e.extract()
        print(self.output_filename)
        self.e.write(self.output_filename)

#@SkipTest
class TestLearning:
    """TEsts the process of learning.
    """

    def setUp(self):
        # print("Learning data taken from:", LEARN_FILES)
        docname = self.docname = LEARN_FILES[0]
        others = LEARN_FILES[1:]
        self.e = XMLTextPropertyExtractor(filename=docname)
        self.others = [XMLTextPropertyExtractor(filename=filename)
                       for filename in others]
        for o in self.others:
            self.e.join_fit(o)

    def tearDown(self):
        pass

    def test_update(self):
        self.e.update(others=True)
        self.e.write(self.docname + "-updated")
        for o in self.e.prop_extractors:
            ofilename=o.filename+"-updated"
            # print("RENEW: {}".format(ofilename))
            o.write(ofilename)

    # def test_learning_params_self(self):
    #     self.e.learning_params(teaching=True)
    #     #[print(x) for x in self.e.learn_coding]
    #     x, y = self.e.prepare_params(teaching=True)
    #     #print(x,y)
    #     assert len(x[0]) > 0 or len(y[0]) > 0
    #     assert len(x) == len(y)
    #     m = self.e.fit()
    #     assert m is not None
    #     recon = self.e.predict(rows=x[:, :])
    #     # print("Declinations:", recon - y)

    def test_predict_on_annotations(self):
        self.e.fit(debug=False)
        for doc_file in FILES:
            xml = XMLTextPropertyExtractor(
                filename=doc_file, importer=tdfodt.Importer)
            output_filename = doc_file.replace("annotations", "out").replace(
                ".odt", "-extracted.xml")
            xml.load()
            xml.extract()
            xml.write(output_filename)
            xml.set_learn_coding(self.e.learn_coding)
            nx = xml.prepare_params()
            ny = self.e.predict(extractor=xml)
            output_filename = doc_file.replace("annotations", "out").replace(
                ".odt", "-predicted.xml")
            xml.write(output_filename)
            assert ny is not None

    def test_predict_on_documens(self):
        global LONG_DOCS
        if not LONG_DOCS:
            print ("Long documents skipped")
            return
        else:
            print ("Processing long documents")

        self.e.fit()
        ldocs=len(DOCS)
        count = LONG_COUNT
        for i, doc_file in enumerate(DOCS):
            #if i!=219:
            #    continue
            print("{} of {}: {}".format(i+1, ldocs, doc_file))
            fp,lp=doc_file.split("annotations/documents/")
            lp.strip(".odt")
            lp=lp.replace(" ","_")
            lp=lp.replace("/","__")
            fn=os.path.join(fp,"out",lp)
            _dp="-document-predicted.xml"
            predicted_filename = fn+_dp
            comment = predicted_filename
            if len(predicted_filename)>50:
                pparts=predicted_filename.split("__",2)
                lpart = pparts.pop(-1)
                fp = lpart.replace(_dp,"")
                f1,middle,f3=fp[:10],fp[10:-10],fp[-10:]
                hh = sha1()
                hh.update(middle.encode("utf-8"))
                middle=hh.hexdigest()
                fp=f1+'_'+middle+'_'+f3
                lpart=fp+_dp
                predicted_filename='__'.join(pparts+[lpart])
            else:
                comment=None
            print("STARTING:",predicted_filename)

            try:
                os.stat(predicted_filename)
                print ("Already done.")
                if LONG_REPLACE:
                    print("... but we will replace it!")
                else:
                    continue
            except OSError:
                pass

            xml = XMLTextPropertyExtractor(filename=doc_file,
                                           importer=tdfodt.Importer)
            try:
                xml.load()
            except etree.XMLSyntaxError:
                print ("Cannot load xml.")
                continue
            xml.extract()
            xml.set_learn_coding(self.e.learn_coding)
            nx = xml.prepare_params()
            ny = self.e.predict(extractor=xml)
            try:
                if comment is not None:
                    root=xml.tree.getroot()
                    comm = etree.Comment("\nOriginal file name:\n\t{}\n".format(comment))
                    root.insert(0, comm)
                xml.write(predicted_filename)
            except OSError as e:
                print("Cannot write:", predicted_filename, e)
                continue
            assert ny is not None
            count-=1
            if count==0:
                print("Count [exhausted] for {}".format(LONG_COUNT))
                break
