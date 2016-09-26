from lxml import etree

_mark=object()

class BaseImporter(object):
    def __init__(self, filename):
        self.doc = None
        self.tree = None
        self.filename = filename

    def load(self):
        if self.doc is not None:
            return

        self._load()
        self.as_xml()

    def as_xml(self):
        self.load()
        root = etree.Element("document")
        tree = self.tree = etree.ElementTree(root)
        self._as_xml(root=root, tree=tree)
        return tree

    def write_xml(self, filename):
        if self.tree is None:
            self.as_xml()
        self.tree.write(
            filename,
            pretty_print=True,
            encoding="UTF-8",
            xml_declaration=True)

    def set(self, e, key, value, default=_mark, pt=None):
        if value is None and default is not _mark:
            value = default
        if value is not None:
            if pt and not isinstance(value, str):
                value = value.pt
            e.set(key, str(value))
