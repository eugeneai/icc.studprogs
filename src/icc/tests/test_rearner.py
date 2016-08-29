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

FILES = glob(os.path.join(DATA_DIR, EXT_PATTERN))


class TestBasicLoad:
    def setUp(self):
        docname = self.docname = FILES[0]
        self.output_filename = \
            self.docname.replace("annotations","out").replace(".docx",".xml")
        self.e = XMLTextPropertyExtractor(
            filename=docname, importer=msdocx.Importer)

    def tearDown(self):
        pass

    def test_load_basic(self):
        self.e.extract()
        self.e.write(self.output_filename)
