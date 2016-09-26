from odf.opendocument import OpenDocumentText, load
#from odf.load import LoadParser
from lxml import etree
from icc.studprogs.importer.base import BaseImporter


class Importer(BaseImporter):
    def _load(self):
        self.doc = load(self.filename)
        return self.doc

    def _as_xml(self, root, tree):
        for item in self.doc.iternodes():
            print(type(item), item.qname)
        return tree
