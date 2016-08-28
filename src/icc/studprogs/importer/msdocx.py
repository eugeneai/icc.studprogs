from lxml import etree
from docx import Document

# from docx.shared import Inches


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
        for par in self.doc.paragraphs:
            p = etree.SubElement(root,"par")
            for run in par.runs:
                r = etree.SubElement(p, "style")
                r.set("id",run.style.name)
                r.set("bold", "1" if run.bold else "0")
                r.set("italic", "1" if run.italic else "0")
                r.set("underline", "1" if run.underline else "0")
                font_name = run.font.name
                if font_name is not None:
                    r.set("font", font_name)
                # TODO Color
                r.text = run.text

        return self.tree

    def write_xml(self, filename):
        if self.tree is None:
            self.as_xml()
        self.tree.write(
            filename,
            pretty_print=True,
            encoding="UTF-8",
            xml_declaration=True)
