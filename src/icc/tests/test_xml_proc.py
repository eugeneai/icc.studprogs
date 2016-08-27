from nose.tools import raises
from pkg_resources import resource_filename
from icc.studprogs.xmlproc import XMLProcessor
from lxml import etree

package = __name__
TEST_FILE1 = resource_filename("icc.studprogs", "data/xml-1-240-059285.xml")
OFILE = TEST_FILE1.replace(".xml", "-{}.xml").replace("data/", "data/out/")


class TestBasicXMLProc:
    def setUp(self):
        self.xml = XMLProcessor(TEST_FILE1)
        self.xml.load()

    def tearDown(self):
        pass

    def test_non_null(self):
        assert self.xml.tree is not None

    def test_get_bbox(self):
        xml = '''
        <page number="1" bbox-left="27" bbox-top="18" bbox-right="562"
          bbox-bottom="718" bbox-width="535" bbox-height="700"
          bounding-box="27 18 562 718" width="595.3199999999999"
          height="841.92"/>
          '''
        xml = etree.XML(xml)
        rc = self.xml.get_bbox(xml)
        assert rc == [27, 18, 535, 700]

    def test_find_indents(self):
        cont = self.xml.find_indents()
        assert cont[0] and cont[1]

    def test_find_indents_with_thr(self):
        cont = self.xml.find_indents(indent_thr=5, tail_thr=5)
        self.xml.write(OFILE.format("thr5"))
        assert cont[0] and cont[1]

    def test_recognition_paragraphs_simple(self, write=True):
        self.xml.find_indents(indent_thr=5, tail_thr=5)
        count = self.xml.simple_par()
        if write:
            self.xml.write(OFILE.format("thr5-simple_par"))
        assert count > 0

    def test_reduce(self):
        self.test_recognition_paragraphs_simple(write=False)
        self.xml.write(OFILE.format("before-reduce-lines"))
        self.xml.reduce_lines()
        self.xml.write(OFILE.format("before-par"))
        self.xml.form_par()
        self.xml.reduce_style()
        self.xml.remove_pages()
        self.xml.style_names()
        self.xml.reduce_pars()
        of=OFILE.format("final")
        self.xml.write(of)
        self.xml.as_xhtml()
        of=OFILE.format("xhtml")
        self.xml.write(of)
