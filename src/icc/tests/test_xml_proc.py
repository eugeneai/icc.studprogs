from nose.tools import raises
from pkg_resources import resource_filename
from icc.studprogs.xmlproc import XMLProcessor
from lxml import etree

package = __name__
TEST_FILE1 = resource_filename("icc.studprogs", "data/xml-1-240-059285.xml")


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
        assert rc == [27,18,535,700]
