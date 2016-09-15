from nose.tools import raises, nottest
from pkg_resources import resource_filename
from icc.studprogs.learn import XMLTextPropertyExtractor
from icc.studprogs.importer import msdocx
from lxml import etree
from nose.plugins.skip import SkipTest
from glob import glob
import os.path

package = __name__
DATA_DIR = resource_filename("icc.studprogs", "data/annotations/")
DOC_DIR = os.path.join(DATA_DIR, "documents")
EXT_PATTERN = "*.docx"
LEARN_PATTERN = "*-learn.xml"

FILES = glob(os.path.join(DATA_DIR, EXT_PATTERN))
DOCS = glob(os.path.join(DOC_DIR, EXT_PATTERN))
LEARN_FILES = glob(os.path.join(DATA_DIR, LEARN_PATTERN))


class TestBasicLoad:
    def setUp(self):
        docname = self.docname = FILES[0]
        self.output_filename = \
            self.docname.replace("annotations","out").replace(".docx",".xml")
        self.e = XMLTextPropertyExtractor(
            filename=docname, importer=msdocx.Importer)

    def tearDown(self):
        pass

    def test_extract_basic(self):
        self.e.extract()
        print(self.output_filename)
        self.e.write(self.output_filename)


class TestLearning:
    """TEsts the process of learning.
    """

    def setUp(self):
        print("Learning data taken from:", LEARN_FILES)
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
        self.e.fit()
        for docx_file in FILES:
            xml = XMLTextPropertyExtractor(
                filename=docx_file, importer=msdocx.Importer)
            output_filename = docx_file.replace("annotations", "out").replace(
                ".docx", "-extracted.xml")
            xml.load()
            xml.extract()
            xml.write(output_filename)
            xml.set_learn_coding(self.e.learn_coding)
            nx = xml.prepare_params()
            ny = self.e.predict(extractor=xml)
            output_filename = docx_file.replace("annotations", "out").replace(
                ".docx", "-predicted.xml")
            xml.write(output_filename)
            assert ny is not None

    def test_predict_on_documens(self):
        # return
        self.e.fit()
        for docx_file in DOCS:
            xml = XMLTextPropertyExtractor(
                filename=docx_file, importer=msdocx.Importer)
            output_filename = docx_file.replace("annotations/documents","out").replace(".docx","-document-extracted.xml")
            xml.load()
            xml.extract()
            xml.write(output_filename)
            xml.set_learn_coding(self.e.learn_coding)
            nx = xml.prepare_params()
            ny = self.e.predict(extractor=xml)
            output_filename = docx_file.replace("annotations/documents","out").replace(".docx","-document-predicted.xml")
            xml.write(output_filename)
            assert ny is not None
