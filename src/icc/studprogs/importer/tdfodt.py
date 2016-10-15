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
        self.reduce(root)

    def iterchildren(self, node, only_nodes=True):
        for e in node.childNodes:
            if e.nodeType == element.Node.ELEMENT_NODE:
                yield e, e.tagName, e.attributes
            elif not only_nodes:
                yield e, None, None

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
        styles=root.xpath("./styles[@imported = 1]")
        if len(styles)>0:
            styles=styles[0]
        else:
            styles=etree.SubElement(root,'styles')
        styles.set("imported","1")
        for e, t, a in self.iterchildren(node):
            if t in ["style:style","style:default-style", "style:list-style", "text:list-style"]:
                name = a.get(('urn:oasis:names:tc:opendocument:xmlns:style:1.0', 'name'), None)
                if name is None:
                    continue
                style=etree.SubElement(styles, "styledef")
                style.set("id", name)
                family=a.get(('urn:oasis:names:tc:opendocument:xmlns:style:1.0', 'family'), None)
                if family is not None:
                    style.set("family", family)
                self.style(e, style)
            else:
                print("styles:", t)
    def style(self, node, root):
        sty=root
        for e, t, a in self.iterchildren(node):
            if t=="style:text-properties":
                fs=a.get(('urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0', 'font-size'), None)
                if fs is not None:
                    sty.set("font-size", fs.replace("pt",''))
                fp=a.get(('urn:oasis:names:tc:opendocument:xmlns:style:1.0', 'font-pitch'),"variable")
                sty.set("font-pitch", fp)
                fn=a.get(('urn:oasis:names:tc:opendocument:xmlns:style:1.0', 'font-name'), None)
                if fn is not None:
                    sty.set("font-name", fn)
                fs=a.get(('urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0', 'font-style'), None)
                if fs is not None:
                    if fs=="italic":
                        sty.set("italic", "1")
                else:
                    sty.set("italic", "0")
                fw=a.get(('urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0', 'font-weight'), None)
                if fw is not None and fw.endswith("bold"):
                    sty.set("bold","1")
                else:
                    sty.set("bold","0")
                fu=a.get(('urn:oasis:names:tc:opendocument:xmlns:style:1.0', 'text-underline-style'), None)
                if fw is not None:
                    sty.set("underline","1")
                else:
                    sty.set("underline","0")
                # print ("TEXT:", a)
            # TODO List styles
            else:
                pass # FIXME Some interpretation of paragraph styles needed
                #print("style:", t,a)

    def settings(self, node, root):
        pass

    def body(self, node, root):
        for e, t, a in self.iterchildren(node):
            if t in {"text:tracked-changes","text:sequence-decls"}:
                continue
            if t in ["office:text","text:section"]:
                self.body(e, root)
            elif t in ["text:p","text:h"]:
                self.p(e, root)
            elif t=="text:list":
                list_=etree.SubElement(root,"list")
                self.list(e,list_)
            elif t=="table:table":
                self.table(e,root)
            else:
                print("body:", e.tagName, a)

    def p(self, node, root):
        par = etree.SubElement(root, "par")
        sty = etree.SubElement(par, "style")
        style = node.attributes[('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'style-name')]
        sty.set("style-id", style)
        self.proc_p(node, par, sty, style)

    def proc_p(self, node, par, sty_, style_):
        if sty_.text is None:
            sty_.text=''
        for e, t, a in self.iterchildren(node, only_nodes=False):
            if t=="text:span":
                sty=etree.SubElement(par, "style")
                style=a[('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'style-name')]
                sty.set("id", style)
                self.proc_p(e, par, sty, style)
                gtext=sty.text
                if gtext.strip():
                    sty_=etree.SubElement(par, "style")
                    sty_.set("style-id", style_)
                    sty_.text=''
                else:
                    par.remove(sty)
                    sty_.text+=gtext
            elif t=="text:a":
                sty=etree.SubElement(par, "style")
                sty.set("id", a[('urn:oasis:names:tc:opendocument:xmlns:text:1.0', 'style-name')])
                URL=a[('http://www.w3.org/1999/xlink', 'href')]
                sty.text=URL
                sty_=etree.SubElement(par, "style")
                sty_.set("style-id", style_)
                sty_.text=''
            elif t=="text:s":
                sty_.text+=" "
            elif e.nodeType == element.Node.TEXT_NODE:
                sty_.text+=e.data
            else:
                print ("par:", t, a, e)

    def list(self, node, root):
        for e, t, a in self.iterchildren(node):
            if t=="text:list-item":
                li=etree.SubElement(root,"li")
                self.list_item(e, li, node)
            else:
                print ("list:", t,a)

    def list_item(self, node, root, list_node):
        for e, t, a in self.iterchildren(node):
            if t in ["text:p","text:h"]:
                self.p(e,root)
            else:
                print ("list-item:", t,a)

    def table(self, node, root):
        table=etree.SubElement(root,"table")
        row=0
        for e, t, a in self.iterchildren(node):
            if t=="table:table-column":
                self.table_column(e,table)
            elif t=="table:table-row":
                self.table_row(e,table,row)
                row+=1
            else:
                print("table:",t,a)

    def table_column(self, node, root):
        for e, t, a in self.iterchildren(node):
            print ("table-column:", t,a)

    def table_row(self, node, root, row):
        col=0
        for e, t, a in self.iterchildren(node):
            if t=="table:table-cell":
                span_rows=a.get(('urn:oasis:names:tc:opendocument:xmlns:table:1.0', 'number-rows-spanned'),'1')
                span_cols=a.get(('urn:oasis:names:tc:opendocument:xmlns:table:1.0', 'number-columns-spanned'),'1')
                cell=etree.SubElement(root, 'cell')
                cell.set("x",str(col))
                cell.set("y",str(row))
                cell.set("w",span_cols)
                cell.set("h",span_rows)
                cell.get("p","-1")
                self.body(e,cell)
                col+=1
            else:
                print ("table-row:", t,a)

    def cell(self, node, root):
        for e, t, a in self.iterchildren(node):
            print("cell:",t,a)

    def reduce(self, tree):
        it=tree.iterfind(".//par/style")
        for style in it:
            par=style.getparent()
            if len(par)==1:
                continue
            if style.text is not None:
                if style.text != "":
                    continue
                par.remove(style)
