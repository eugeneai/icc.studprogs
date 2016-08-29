from nose.tools import raises, nottest
from pkg_resources import resource_filename
from icc.studprogs.importer.msdocx import Importer
from icc.studprogs.xmlproc import XMLProcessor
from lxml import etree
from nose.plugins.skip import SkipTest
from glob import glob
import os.path

package = __name__
DATA_DIR = resource_filename("icc.studprogs", "data/annotations/")
EXT_PATTERN = "*.docx"

FILES = glob(os.path.join(DATA_DIR, EXT_PATTERN))


class TestFileToBeLoaded:
    def test_files(self):
        docs = [Importer(f) for f in FILES]
        list(map(lambda x: x.load(), docs))
        for d, f in zip(docs, FILES):
            assert d.doc is not None, "loading file {} failed".format(f)


class TestBasicLoad:
    def setUp(self):
        docname = self.docname = FILES[0]
        self.output_filename = \
            self.docname.replace("annotations","out").replace(".docx",".xml")
        self.doc = Importer(docname)

    def tearDown(self):
        pass

    def test_load_basic(self):
        self.doc.load()
        assert self.doc.doc is not None

    def test_xml_conversion(self):
        self.doc.as_xml()
        assert self.doc.tree is not None

    def test_save_xml(self):
        fn = self.output_filename
        self.doc.write_xml(fn)

    def test_import_with_reduction(self):
        fn = self.output_filename.replace(".xml", "-reduced.xml")
        tree = self.doc.as_xml()
        assert tree is not None
        xml = XMLProcessor(tree=tree)
        xml.reduce_style()
        # xml.remove_pages()
        # xml.style_names()
        # xml.reduce_pars()
        xml.write(fn)
