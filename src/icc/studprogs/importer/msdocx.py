from lxml import etree
from docx import Document
from docx.shared import Pt

# from docx.shared import Inches

_mark = object()


class Importer(object):
    def __init__(self, filename):
        self.filename = filename
        self.doc = None
        self.tree = None

    def load(self):
        """Lazy loading routine
        """
        if self.doc is not None:
            return

        self.doc = Document(self.filename)

    def as_xml(self):
        if self.doc is None:
            self.load()
        root = etree.Element("document")
        self.tree = etree.ElementTree(root)
        for section in self.doc.sections:
            s = etree.SubElement(root, "section")
            s.set("type", str(section.start_type))
            # self._section(self, section, s)
        self._paragraphs(root, self.doc.paragraphs)
        for table in self.doc.tables:
            t = etree.SubElement(root, "table")
            nrows, ncols = [len(x) for x in [table.rows, table.columns]]
            t.set("num-rows", str(nrows))
            t.set("num-columns", str(ncols))
            # cell_map = {}
            for nrow in range(nrows):
                ncol = 0
                for ncol in range(ncols):
                    cell = table.cell(nrow, ncol)
                    # c = cell_map.setdefault(ctext, etree.SubElement(t, "cell"))
                    c = etree.SubElement(t, "cell")
                    self.set(c, "x", ncol)
                    self.set(c, "y", nrow)
                    self.set(c, "w", 0)
                    self.set(c, "h", 0)
                    self.set(c, "p", -1)
                    self._paragraphs(c, cell.paragraphs)

        return self.tree

    def _paragraphs(self, parent, paragraphs):
        for par in paragraphs:
            p = etree.SubElement(parent, "par")
            par_format = par.paragraph_format
            self.set(p, "indent", par_format.first_line_indent, "0", pt=True)
            self.set(p, "left-indent", par_format.left_indent, "0", pt=True)
            self.set(p, "right-indent", par_format.right_indent, "0", pt=True)
            self.set(p, "space-before", par_format.space_before, "0", pt=True)
            self.set(p, "space-after", par_format.space_after, "0", pt=True)
            for run in par.runs:
                r = etree.SubElement(p, "style")
                r.set("id", run.style.name)
                r.set("bold", "1" if run.bold else "0")
                r.set("italic", "1" if run.italic else "0")
                r.set("underline", "1" if run.underline else "0")
                self.set(r, "font-name", run.font.name)
                self.set(r, "font-size", run.font.size, pt=True)
                # TODO Color
                r.text = run.text

    def set(self, e, key, value, default=_mark, pt=None):
        if value is None and default is not _mark:
            value = default
        if value is not None:
            if pt and not isinstance(value, str):
                value = value.pt
            e.set(key, str(value))

    def write_xml(self, filename):
        if self.tree is None:
            self.as_xml()
        self.tree.write(
            filename,
            pretty_print=True,
            encoding="UTF-8",
            xml_declaration=True)
