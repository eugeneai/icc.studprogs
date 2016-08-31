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
EXT_PATTERN = "*.docx"
LEARN_PATTERN = "*-learn.xml"

FILES = glob(os.path.join(DATA_DIR, EXT_PATTERN))
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
        self.e.write(self.output_filename)

class TestLearning:
    """TEsts the process of learning.
    """

    def setUp(self):
        docname = self.docname = LEARN_FILES[0]
        self.e = XMLTextPropertyExtractor(filename=docname)

    def tearDown(self):
        pass

    def test_update(self):
        self.e.update()
        self.e.write(self.docname+"-updated")

    def test_learning_params_self(self):
        self.e.learning_params(teaching=True)
        x, y = self.e.prepare_params(teaching=True)
        assert len(x[0]) > 0 or len(y[0]) > 0
        assert len(x) == len(y)
        m = self.e.fit()
        assert m is not None
        recon = self.e.predict(rows=x[:, :])
#        print("Original:", y)
#        print("Predicted:", recon)
#        print("Declinations:", recon - y)
        for docx_file in FILES:
            xml = XMLTextPropertyExtractor(
                filename=docx_file, importer=msdocx.Importer)
            output_filename = docx_file.replace("annotations","out").replace(".docx","-extracted.xml")
            xml.load()
            xml.extract()
            xml.write(output_filename)
            xml.set_learn_coding(self.e.learn_coding)
            nx = xml.prepare_params()
            ny = self.e.predict(extractor=xml)
            output_filename = docx_file.replace("annotations","out").replace(".docx","-predicted.xml")
            xml.write(output_filename)
            assert ny is not None
