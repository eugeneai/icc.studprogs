from odf.opendocument import OpenDocumentText, load
#from odf.load import LoadParser
from lxml import etree
from icc.studprogs.importer.base import BaseImporter
import odf.element as element

SKIP_TAGS = {"office:scripts", "office:font-face-decls"}
class Importer(BaseImporter):
    def _load(self):
        self.doc = load(self.filename)
        # topnode = self.doc.topnode
        return self.doc

    def _as_xml(self, root, tree):
        print(self.filename)
        self.document(self.doc.topnode, root)

    def iterchildren(self, node):
        for e in node.childNodes:
            if e.nodeType == element.Node.ELEMENT_NODE:
                yield e, e.tagName, e.attributes

    def document(self, node, root):
        for e, t, a in self.iterchildren(node):
            if t in SKIP_TAGS:
                continue
            if t=="office:meta":
                self.meta(e, root)
            elif t in {"office:master-styles", "office:automatic-styles", "office:styles"}:
                self.styles(e, root)
            elif t=="office:body":
                self.body(e, root)
            elif t=="office:settings":
                self.settings(e, root)
            else:
                print("Document", e.tagName, a)

    def meta(self, node, root):
        """
        """

    def styles(self, node, root):
        pass

    def settings(self, node, root):
        pass

    def body(self, node, root):
        for e, t, a in self.iterchildren(node):
            if t=="office:text":
                self.body(e, root)
            if t in {"text:tracked-changes","text:sequence-decls"}:
                continue
            if t == "text:p":
                self.p(e, root)
            elif t=="text:list":
                self.list(e,root)
            else:
                print("body:", e.tagName, a)

    def p(self, node, root):
        par = etree.SubElement(root, "par")
        style = node.attributes[('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'style-name')]
        par.set("style-id", style)
        for e, t, a in self.iterchildren(node):
            if t=="text:span":
                sty=etree.SubElement(par, "style")
                sty.set("id", a[('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'style-name')])
                text=''
                for tt in e.childNodes:
                    if tt.nodeType == element.Node.TEXT_NODE:
                        text+=tt.data
                sty.text=text
            else:
                print ("par:", t, a)

    def list(self, node, root):
        for e, t, a in self.iterchildren(node):
            if t=="text:list-item":
                self.list_item(e, root, node)
            else:
                print ("list:", t,a)

    def list_item(self, node, root, list_node):
        for e, t, a in self.iterchildren(node):
            print ("list-item:", t,a)
