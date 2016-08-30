import icc.studprogs.popplerxml as loader
import icc.studprogs.textloader as textloader
# import pybison
from pkg_resources import resource_stream
from lxml import etree

from icc.studprogs.xmlproc import XMLProcessor
import numpy as np

from itertools import islice, cycle
import sys
import pymorphy2
from sklearn import tree
import pprint

import icc.linkgrammar as lg
import icc.studprogs.uctotokenizer as ucto
from icc.studprogs.common import paragraph_symbol, Symbol
import re
import locale
locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

package = __name__
TEST_FILE1 = resource_stream("icc.studprogs", "data/059285.txt")
TEST_FILE2 = resource_stream("icc.studprogs", "data/059285.xml")
TEST_FILE3 = resource_stream("icc.studprogs", "data/grin.txt")


class MorphologicalTagger(object):
    """Tag a lexems in a stream morphoogically
    by means of pymorphy2.
    """

    def __init__(self, lexemiterator):
        """Initialize class with
        lexem iterator source
        """
        self.lexemiterator = lexemiterator
        self.analyzer = None

    def paragraphs(self):
        """Tag each token morphologically
        and construct paragraph again. # FIXME Write it more clear.
        """
        self.analyzer = pymorphy2.MorphAnalyzer()
        for paragraph in self.lexemiterator.paragraphs():
            yield self._tag(paragraph)

    def _tag(self, par):
        new_par = []
        for lexeme in par:
            if isinstance(lexeme, tuple):
                token, attrs = lexeme
                tok = str(token)
                rc = self.analyzer.parse(tok)
                new_par.append((token, attrs.new_child({"morph": rc})))
            else:
                new_par.append(lexeme)
        return new_par


class LinkGrammar(object):
    """
    """

    def __init__(self, iterator, lang="ru", only_valid=True):
        """Initialize class with
        paragraph iterator source
        """
        self.iterator = iterator
        self.lg = lg.LinkGrammar(lang)
        self.make_options()
        self.lang = lang
        self.analyzer = None
        self._maxlinkages = 1
        self._linkages = self._maxlinkages
        self.only_valid = only_valid

    def make_options(self):
        self.lg.linkage_limit = 1
        # self.lg.max_parse_time=10
        self.lg.verbosity = 1
        # self.lg.setup_abiword_main() # self.lg.setup_abiword_main()

        # self.lg.disjunct_cost=2.0
        self.lg.min_null_count = 0
        self.lg.max_null_count = 100
        self.lg.islands_ok = 1
        self.lg.max_parse_time = 2

        self.lg.reset_resources()
        pass
        # self.options=lg.ParseOptions(linkage_limit=1,
        #                              verbosity=0,
        #                              islands_ok=True,
        #                              max_parse_time=10)

    def linkages(self, text):
        """Analyses one sentence.

        Arguments:
        - `text`: Input sentence.
        """
        # dictionary=lg.Dictionary(self.lang)
        # self.make_options()
        self.lg.reset_resources()
        self.lg.parse(text)
        # rc = sent.split()
        # if rc < 0:
        #     print ("--- Cannot split ---")
        #     del sent
        #     return iter(())

        print("V:", self.lg.num_valid, "L:", self.lg.num_linkages)
        print(repr(text))
        if self.only_valid:
            for i in range(min(self.lg.num_valid, self._maxlinkages)):
                yield True, i, self.lg
        else:
            v = self.lg.num_valid
            for i in range(min(self.lg.num_linkages, self._maxlinkages)):
                print(i, v)
                yield i < v, i, self.lg

    def __call__(self, verbose=0):
        for par in self.iterator:
            if not isinstance(par, str):
                continue
            par = par.strip()
            if not par:
                continue
            if verbose:
                print("PAR:", repr(par))

            for rc, num, _lg in self.linkages(par):
                if rc:
                    linkage = _lg.diagram(num) + "\n" + _lg.pp_msgs(num)
                else:
                    linkage = None

                if verbose:
                    if rc:
                        print("----SUCCEED------")
                    else:
                        print("----FAILED------")
                yield par, rc, linkage


SECTION_RE = re.compile("(^(\d+\.?)+)")
WORD_OPK = re.compile("\((о?п?к.+\d+)\)")
SPACE_LIKE_RE = re.compile("(\s|\n|\r)+")


class LearningData(object):
    def __init__(self):
        self.encoding = {
        }  # {feature-name -> (feature-index, {feature-value -> feature-code})}
        self.decoding = {}  # {feature-index -> (name, {code->value})}

    def encode(self, name, value, teaching=False):
        if name in CONVERT_VALUE:
            f = CONVERT_VALUE[name]
            if f is None:  # Filtered out field
                return None, None
            value = f(value)
        elif "_" in CONVERT_VALUE:
            try:
                value = CONVERT_VALUE["_"](value)
            except ValueError:
                pass
        if teaching:
            idx, codes = self.encoding.setdefault(name,
                                                  (len(self.encoding), {}))
        elif name in self.encoding:
            idx, codes = self.encoding[name]
            if value in codes:
                return idx, codes[value]
            return None, None
        else:
            return None, None
        # zero value reserved for unknowns
        code = codes.setdefault(value, len(codes) + 1)
        d = self.decoding.setdefault(idx, (name, {}))
        d[1][code] = value
        return idx, code

    def index(self, name):
        return self.encoding[name][0]

    def name(self, index):
        return self.decoding[index][0]

    def decode(self, index, code):
        if isinstance(index, str):
            index = self.index(index)
        name, d = self.decoding[index]
        return name, d[code]

    def __str__(self):
        s = "A " + self.__class__.__name__ + " object \n"
        l = "=" * len(s) + "\n\n"
        s += l
        s += "encoding:" + pprint.pformat(self.encoding, indent=2)
        s += "\n"
        s += "decoding:" + pprint.pformat(self.decoding, indent=2)
        s += "\n"
        s += l
        return s


def as_number(x):
    try:
        return int(x)
    except ValueError:
        pass
    try:
        return float(x)
    except ValueError:
        return x


def round_indent(x, round_val=0.5 * 72):  # I.e. 72 pt * 0.5 in
    x = float(x)
    xx = round(x / round_val)
    x = int(xx) * round_val
    return x


CONVERT_VALUE = {
    # 'alignment': lambda x: x.split(" ")[0].lower(),
    'alignment': None,
    'section-mark': lambda x: x,
    'indent': round_indent,
    'left-indent': round_indent,
    'right-indent': round_indent,
    'space-after': None,
    'space-before': None,
    'widow-control': None,
    "_": as_number,
}


class XMLTextPropertyExtractor(object):
    def __init__(self, tree=None, filename=None, importer=None, lang="ru"):
        if tree is None and filename is None:
            raise ValueError("either tree or filename must be set")
        self.tree = tree
        self.filename = filename
        self.importer = importer
        self.morph = pymorphy2.MorphAnalyzer()
        self.tokenizer = ucto.Tokenizer()
        self.xmlprocessor = None
        self.learn_coding = None

    def load(self):
        if self.tree is not None:
            return self.tree
        if self.importer is None:
            self.tree = etree.parse(self.filename)
        else:
            importer = self.importer(self.filename)
            importer.load()
            self.tree = importer.as_xml()
        if self.xmlprocessor is None:
            self.xmlprocessor = XMLProcessor(tree=self.tree)
        return self.tree

    def par_process(self, proc_list):
        self.load()
        for par in self.tree.iterfind("//par"):
            text = etree.tostring(par, method="text", encoding=str)
            ntext, words, tokens = self.preporocess_text(text)
            for p in proc_list:
                if isinstance(p, tuple):
                    args = p[1:]
                    p = p[0]
                else:
                    args = []
                p(par, ntext, words, tokens, *args)

    def words(self, text, with_tokens=False):
        t = SPACE_LIKE_RE.sub(" ", text)
        # TODO
        for token in self.tokenizer.tokens([t]):
            w = str(token)
            if token.type().startswith("WORD"):
                p = self.morph.parse(w)[0]
                w = p.normal_form
            if with_tokens:
                yield w, token
            else:
                yield w

    def preporocess_text(self, text):
        t = ""
        tokens = list(self.words(text, with_tokens=True))
        for word, token in tokens:
            t += word
            if not token.nospace():
                t += " "
        return t, [t[0] for t in tokens], [t[1] for t in tokens]

    def par_has_section_mark(self, par, text, words, tokens):
        m = SECTION_RE.search(text)
        if m:
            mark = m.group(1)
            par.set("section-mark", mark)
            mark = mark.rstrip(".")
            cnt = mark.count(".")
            cnt += 1
            par.set("section-level", str(cnt))

    def par_has_words(self, par, text, words, tokens, find_words=[]):
        for w in find_words:
            if w in words:
                par.set("word-" + w, "1")

    def par_is_empty(self, par, text, words, tokens):
        if len(words) == 0:
            par.set("par-is-empty", "1")
        for t in tokens:
            if t.type().startswith("WORD"):
                return
        par.set("no-words", "1")

    def par_opk_marks(self, par, text, words, tokens):
        m = WORD_OPK.search(text)
        if m is not None:
            par.set("opk-sign", "1")
            par.set("opk", m.group(1))

    def par_has_compounds(self,
                          par,
                          text,
                          words,
                          tokens,
                          compounds,
                          dist=0,
                          op=None):
        lwords = len(words)
        if lwords == 0:
            return
        for comp in compounds:
            lcomp = len(comp)
            if lcomp > lwords:
                continue
            first_comp = comp[0]
            for i in range(lwords):
                # print(words[i], first_comp)
                if words[i] != first_comp:
                    continue
                # print("b", words[i:4], comp)
                lastpos = i + lcomp - 1
                try:
                    if words[lastpos] != comp[-1]:
                        continue
                except IndexError:
                    break
                # print("e:", words[i+1:lastpos], comp[1:-1])
                if words[i + 1:lastpos] != comp[1:-1]:
                    continue
                # print("w:")
                par.set("compound-" + "-".join(comp), "1")
                break

    def extract(self, style_names=True):
        self.load()
        par_processors = [
            self.par_has_section_mark, self.par_opk_marks, self.par_is_empty,
            (self.par_has_words,
             ["знать", "уметь", "владеть", "технология", "оценочный",
              "средства", "ресурс", "интернет", "квалификация", "овладеть",
              "освоить", "изучить", "формировать", "способный",
              "совершенствовать", "понимать", "метод", "применение", "тема",
              "раздел", "перечень", "лабораторный", "практический", "лекция",
              "лекционный", "семинарский", "предусмотренный", "занятие",
              "самостоятельный", "подготовка", "доклад", "экзамен", "зачет",
              "оформление", "занятие", "оценочный", "средство",
              "информационный", "обеспечение", "основной", "информационный",
              "дополнительный", "электронный", "ресурс", "цель", "задача"]), (
                  self.par_has_compounds, list(
                      map(lambda x: x.split(" "), [
                          "рабочий программа дисциплина",
                          "специальность высший образование",
                          "программа магистратура", "программа бакалавриат",
                          "программа дисциплина", "задачи освоение дисциплина",
                          "компетенция обучающийся", "обучающийся должный",
                          "структура дисциплина", "содержание дисциплина",
                          "оценочный средство", "код и наименование",
                          "наименование дисциплина", "указать профиль"
                      ])))
        ]
        self.xmlprocessor.reduce_style()
        self.par_process(par_processors)
        if style_names:
            self.xmlprocessor.style_names()

    def update(self):
        self.extract(style_names=False)

    def learning_params(self, teaching=False):
        self.load()
        param_coding = LearningData()
        target_coding = LearningData()
        self.learn_coding = (param_coding, target_coding, teaching)

        for par in self.tree.iterfind("//par"):
            for k, v in par.attrib.items():
                if k.startswith("t-"):
                    target_coding.encode(k, v, teaching=teaching)
                else:
                    param_coding.encode(k, v, teaching=teaching)

    def set_learn_coding(self, learn_coding):
        self.learn_coding = learn_coding

    def prepare_params(self, teaching=False):
        self.load()
        param_coding, target_coding, _ = self.learn_coding
        lparam_coding = len(param_coding.encoding)
        ltarget_coding = len(target_coding.encoding)
        param_rows = []
        if teaching:
            target_rows = []
        par_index = {}
        for par in self.tree.iterfind("//par"):
            param_row = [0] * lparam_coding
            if teaching:
                target_row = [0] * ltarget_coding
            a = par.attrib
            for k, v in a.items():
                if k.startswith("t-"):
                    if not teaching:
                        continue
                    i, code = target_coding.encode(k, v)
                    if i is not None:
                        target_row[i] = code
                else:
                    i, code = param_coding.encode(k, v)
                    if i is not None:
                        param_row[i] = code
            if len([x for x in param_row if x != 0]) == 0:
                continue
            if teaching and len([x for x in target_row if x != 0]) == 0:
                continue
            l = len(param_rows)
            par_index[l] = par
            param_rows.append(param_row)
            if teaching:
                target_rows.append(target_row)

        param_rows = np.array(param_rows, dtype=np.uint8)
        if teaching:
            target_rows = np.array(target_rows, dtype=np.uint8)
            return param_rows, target_rows
        return param_rows, par_index

    def fit(self, method="tree"):
        """Prepare parameters for fitting and make a fit.
        """
        if self.learn_coding is None:
            self.learn_coding(teaching=True)
        x, y = self.prepare_params(teaching=True)
        clf = tree.DecisionTreeClassifier()
        clf = clf.fit(x, y)
        self.fit_model = clf
        return clf

    def predict(self, rows=None, par=None, extractor=None):
        """Apply learning models to a rows of encoded values or
        to a paragraph or to a xml tree adding the atttributes
        from fitting.
        """
        if rows is not None:
            return self.fit_model.predict(rows)
        if extractor is not None:
            extractor.extract()
            extractor.set_learn_coding(self.learn_coding)
            x, par_index = extractor.prepare_params()
            y = self.predict(rows=x)
            extractor.interprete(y, par_index)
            return extractor.tree

    def interprete(self, rows, par_index):
        target_coding = self.learn_coding[1]
        for idx, par in par_index.items():
            row = rows[idx]
            for i, val in enumerate(row):
                i = int(i)
                val = int(val)
                if val == 0:
                    continue
                name, value = target_coding.decode(i, val)
                value = str(value)
                par.set(name, value)
        return self.tree

    def write(self, filename):
        self.tree.write(
            filename,
            pretty_print=True,
            encoding="UTF-8",
            xml_declaration=True)


def _print(par, rc, linkage):
    """
    """

    print("PAR:", par)
    if linkage:
        print(rc, linkage)
        if not rc:
            print("MSG:!!")
    else:
        print("---NO LINKAGE---")


def tokenize_test(stream, loader_class, limits):
    l = loader_class(stream)
    g = (ucto.join(sent, with_type=True) for sent in l.sentences())
    for sent in islice(g, limit):
        if isinstance(sent, str):
            print(sent)


def link_parsing1(stream, loader_class, limits):
    l = loader_class(stream)
    linkgram = LinkGrammar(
        (ucto.clean_join(sent) for sent in l.sentences()), only_valid=False)
    linkgram = islice(linkgram(verbose=0), limit)
    for par, rc, linkage in linkgram:
        _print(par, rc, linkage)


def link_parsing11(stream, loader_class, limits):
    l = loader_class(stream)
    for par in l.paragraphs(join=True, style="hidden", only_words=False):
        print(par)


def link_parsing2(_1, _2, limits):
    sent1 = '''Производственная практика проводится в структурных
    подразделениях ИРНИТУ или других организациях.
    Для выполнения заданий самостоятельной работы по производственной
    практике вуз обеспечивает свободный доступ к библиотечным фондам,
    к сети Интернет и базам данных вуза и кафедры.'''
    sent2 = '''Богатство заключается в многообразии потребностей и желаний.'''
    sent3 = "Итогом преддипломной практики является выпускная "\
            "квалификационная работа ."
    linkgram = LinkGrammar([sent3, sent1, sent2], only_valid=False)
    linkgram = islice(linkgram.paragraphs(verbose=0), limit)

    for par, rc, linkage in linkgram:
        _print(par, rc, linkage)


def test_sentence(stream, loader_class, limits):
    l = loader_class(
        stream,
        line_paragraph=False,
        empty_line_paragraph=False, )
    # l.skip(200)
    for sent in islice(l.sentences(), limits):
        if isinstance(sent, Symbol):
            if sent == paragraph_symbol:
                print()
            else:
                print("->", sent)
        else:
            print(ucto.join(sent, no_symbols=True))


def main(stream, loader_class, limit):
    """

    Arguments:
    - `stream`: open stream to learn from
    """
    l = loader_class(stream)
    mt = MorphologicalTagger(l)
    for paragraph in islice(mt.paragraphs(), limit):
        for word in paragraph:
            try:
                token, attrs = word
                t = str(token)
                m = attrs["morph"]
                t = t
                # t=t+"/"+str(m[0].normal_form)
                # t=str(m[0].normal_form)
            except TypeError:
                t = str(word.mark())
            print(t, end=" ")
        print("\n" + "-" * 20)


def debug_reverse(iterator):
    r = reversed(list(iterator))
    yield from r


if __name__ == "__main__":
    limit = 20000000
    # main(TEST_FILE1, limit)
    link_parsing11(TEST_FILE2, loader.Loader, limit)
    # tokenize_test(TEST_FILE2, loader.Loader, limit)
    # link_parsing1(TEST_FILE3, textloader.Loader, limit)
    # test_sentence(TEST_FILE2, loader.Loader, limit)
    quit()
