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
from sklearn import tree, svm
from sklearn.naive_bayes import GaussianNB
import pprint

import icc.linkgrammar as lg
import icc.studprogs.uctotokenizer as ucto
from icc.studprogs.common import paragraph_symbol, Symbol
import re
import locale
locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

USE_TREE = True # Use decision trees for learning

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


SECTION_RE = re.compile("^(.{0,8}?)(\d{1,2}(\.\d{1,2}){0,1}\.?)[ \t]")
BAD_PREAMBLE_RE = re.compile("^.*?\d+$")
WORD_PREAMBLE_RE = re.compile("^.*?(\w+).*?$")
WORD_OPK = re.compile("\((о?п?к.+\d{1,2})\)")
SPACE_LIKE_RE = re.compile("(\s|\n|\r)+")

NS = {
    None: "http://irnok.net/data/document-structure",
    "dcterms": "http://purl.org/dc/terms/",
    "dctypes": "http://purl.org/dc/dcmitype/",
    "dc": "http://dublincore.org/2012/06/14/dcelements.rdf",
}

# Interpretations
# dcterms:contributor,creator,title
# dc:Title
# dcterms:bibliographicCitation,rightsHolder
# dctypes:Text # Get vslue as text of paragraph
# dctypes:Software
# bf:Title, bf:title

# deo:caption

# http://www.sparontologies.net/ontologies - Description of published matter.
#

# Document description ontologies http://www.semantic-web-journal.net/system/files/swj1016_0.pdf

# pimspace: http://www.w3.org/ns/pim/space#     # Not found
# # # fabio: http://purl.org/spar/fabio/ oa: http://www.w3.org/ns/oa# as: http://www.w3.org/ns/activitystreams# ldp: http://www.w3.org/ns/ldp#

# RDFa is the basis of the following interpretation (by example)

# <... property="dc:title">...Title...</...
# <... rel="foaf:topic" href=.... content=... ...>....value...</....
# <... prefix="foaf: http://xmlns.com/foaf/0.1/ dc: http://purl.org/dc/terms/" ...>
# rev= is opposite direction w.r.t. rel=
# <... datatype="xsd:dateTime" ....> ... of literal
# <... about="urn:ISBN:0091808189" ...> - another document inside
# <... typeof="dc:Title" ...>
# <... vocab="http://xmlns.com/foaf/0.1/" ....>
# <... resource="http://dbpedia.org/resource/German_Empire" ...> - Create new Subject

# Feature interpretation

INTERP={
    "annotation-declaration":{
        "a":"schema:TechArticle doap:Project"
    },
    "discipline-study-program":{
        "a":"schema:TechArticle doap:Project",
        "" : "NEXT"
    },
    "discipline-name":{
        "a":"dc:Title",
        "rel":"dc:title schema:name doap:name"
    },
    "training-direction":{
        "rel":"dc:title schema:name doap:name",
        "a":"dc:Title",
        "" : "NEXT"
    },
    "training-direction-name":{
        "a":"dctypes:Text",
    },
    "author": {
        "rel":"schema:creator schema:publisher schema:contributor schema:author",
        "a":"foaf:Person"
    },
    "discipline-program":{
        "rel":"dc:title schema:name doap:name",
        "a":"dc:Title",
        "":"NEXT"
    },
    "discipline-program-name":{
        "a":"dctypes:Text",
    },
    "study-qualification":{

    }
}


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

    def target_coding(self, index=0):
        name, codes = self.decoding[index]
        codes = list(codes.items())
        codes.sort()
        # print ("RC:", rc)
        return [c[1] for c in codes]

    def source_coding(self):
        names = list(self.decoding.items())
        names.sort()
        names = [i[1][0] for i in names]
        # print(names)
        return names

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
    'contextual-section-mark': lambda x: x,
    'indent': None,
    'left-indent': None,
    'right-indent': None,
    'space-after': None,
    'space-before': None,
    'widow-control': None,
    'par-is-empty': None,
    'no-words': None,
    "_": as_number,
}
CONTEXTUAL_FEATURES = set(["section-mark", ])

FIXED_ATTRS = {
    "indent", "left-indent", "right-indent", "space-before", "space-after",
    "widow-control"
}

TOKENISER = None


class XMLTextPropertyExtractor(object):
    def __init__(self, tree=None, filename=None, importer=None, lang="ru"):
        global TOKENISER
        if tree is None and filename is None:
            raise ValueError("either tree or filename must be set")
        self.tree = tree
        self.filename = filename
        self.importer = importer
        self.morph = pymorphy2.MorphAnalyzer()
        if TOKENISER is None:
            TOKENISER = ucto.Tokenizer()
        self.tokenizer = TOKENISER
        self.xmlprocessor = None
        self.learn_coding = None
        self.extracted = False
        self.prop_extractors = []
        self.styles = None

    def load(self):
        for o in self.prop_extractors:
            o.load()
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
        self.load_styles()
        return self.tree

    def load_styles(self):
        if self.styles is None:
            self.styles = s = {}
            for sd in self.tree.iterfind("//styledef"):
                s[sd.get("id")] = sd.attrib

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
        if text is None:
            return
        t = SPACE_LIKE_RE.sub(" ", text)
        for token in self.tokenizer.tokens([t]):
            w = str(token)
            if token.type().startswith("WORD"):
                p = self.morph.parse(w)
                token.morph = p
                w = p[0].normal_form
            if with_tokens:
                yield w, token
            else:
                yield w

    def rake_prases(self, text, stop_words, stop_werb=True, genitiv=True):
        phrase = []
        prevcase = None
        for word, token in self.words(text, with_tokens=True):
            ttype = token.type()
            shift = word not in stop_words and (ttype.startswith("WORD") or
                                                ttype == "ABBREVIATION")
            while not shift:
                p = token.morph
                mf = p[0]
                if mf.tag in {'COMP', 'VERB', 'INFN', 'PRTS', 'GRND', 'NUMR',
                              'NPRO', 'PRED', 'PREP', 'CONJ', 'PRCL', 'INTJ'}:
                    shift = True
                    break
                phrase.append(word)
                if 'ADVB' in mf.tag:
                    break
                if 'NOUN' in mf.tag and mf.case == "gent":
                    yield phrase
                    break
                if mf.tag in {'ADJF', 'ADJS'} and mf.case == 'gent':
                    break
                raise RuntimeError(mf.tag)
            if shift:
                prevcase = None
            if shift and phrase:
                yield phrase
                phrase = []
        if phrase:
            yield phrase

    def preporocess_text(self, text):
        t = ""
        tokens = list(self.words(text, with_tokens=True))
        for word, token in tokens:
            t += word
            if not token.nospace():
                t += " "
        return t.strip(), [t[0] for t in tokens], [t[1] for t in tokens]

    def par_has_section_mark(self, par, text, words, tokens):
        m = SECTION_RE.match(text)
        if m:
            mark = m.group(2)
            preamble = m.group(1)

            if BAD_PREAMBLE_RE.match(
                    preamble) is not None:  # A bad garbage ends with numbers.
                return
            wm = WORD_PREAMBLE_RE.match(preamble)
            if wm is not None:
                word = wm.group(1)
                par.set("section-type", word.lower())
            mark = mark.rstrip(".")
            par.set("section-mark", mark)
            cnt = mark.count(".")
            cnt += 1
            par.set("section-level", str(cnt))
            # print(etree.tostring(par, encoding=str))

    def par_has_URL_or_email(self, par, text, words, tokens):
        for token in tokens:
            t = token.type()
            if t.startswith("URL"):
                par.set("has-url", "1")
            elif t.startswith("E-MAIL"):
                par.set("has-email", "1")

    def par_has_words(self, par, text, words, tokens, find_words=[]):
        for w in find_words:
            if w in words:
                par.set("word-" + w, "1")

    def par_is_empty(self, par, text, words, tokens):
        if len(words) == 0:
            par.set("par-is-empty", "1")
        no_words = True
        for token in tokens:
            t = token.type()
            if t.startswith("WORD"):
                no_words = False
                return
        if no_words:
            par.set("no-words", "1")

    def par_only_numbers(self, par, text, words, tokens):
        if len(words) == 0:
            return
        for token in tokens:
            t = token.type()
            if not t.startswith("NUMBER"):
                return
        par.set("only-numbers", "1")

    def par_has_no_verbs(self, par, text, words, tokens):
        if len(words) == 0:
            return
        has_words = False
        for token in tokens:
            try:
                p = token.morph
            except AttributeError as a:
                continue
            tag = p[0].tag
            if tag.POS == "VERB":
                return
            has_words = True
        if has_words:
            par.set("has-no-verbs", "1")

    def par_opk_marks(self, par, text, words, tokens):
        m = WORD_OPK.search(text)
        if m is not None:
            par.set("opk-sign", "1")
            par.set("opk", m.group(1))

    def par_text_styles(self, par, text, words, token):
        textsize = {'italic': [0, 0], 'bold': [0, 0], 'underline': [0, 0]}
        ttl = 0
        t = ""
        for style in par.iterfind("./style"):
            sid = style.get("id")
            # print(sid, etree.tostring(style, encoding=str))
            a = {}
            if sid is not None:
                attrib = self.styles.get(sid, {})
                a.update(attrib)
            a.update(style.attrib)
            attrib = a
            # print(attrib)
            tt = self.preporocess_text(style.text)[0]
            tl = len(tt)
            t += tt
            ttl += tl
            for sm in textsize.keys():
                v = attrib.get(sm, "0")
                if v == "0":
                    v = 0
                else:
                    v = 1
                textsize[sm][v] += tl
        l = list(textsize.items())
        l.sort(key=lambda x: x[1][1], reverse=True)
        mostkey = l[0][0]
        mostval = l[0][1][1]
        if mostval > 0:
            hf = ttl // 2
            mosts = [i[0] for i in l if i[1][1] >= hf]
            for m in mosts:
                par.set(m, "1")
            # print(par.attrib, t)

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

    def extract(self, update=False):
        self.load()
        if self.extracted and not update:
            return
        par_processors = [
            self.par_has_section_mark,
            self.par_opk_marks,
            # self.par_is_empty,
            self.par_has_URL_or_email,
            self.par_only_numbers,
            self.par_has_no_verbs,
            self.par_text_styles,
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
              "дополнительный", "электронный", "ресурс", "цель", "задача",
              "рисунок", "таблица", "аннотация", "рабочий", "учебный",
              "бакалавр", "магистр", "специалист", "аспирант", "профессор",
              "код", "наименование", "профиль", "указать","примечание","фонд","балл","рейтинг",
              "университет", "министерство", "директор", "институт", "факультет","кафедра"]),
            (self.par_has_compounds, list(
                map(lambda x: x.split(" "), [
                    "рабочий программа дисциплина",
                    "специальность высший образование",
                    "программа магистратура",
                    "программа бакалавриат",
                    "программа дисциплина",
                    "задачи освоение дисциплина",
                    "компетенция обучающийся",
                    "обучающийся должный",
                    "структура дисциплина",
                    "содержание дисциплина",
                    "оценочный средство",
                    "российский федерация",
                    "министерство образование",
                    "наименование дисциплина",
                    "директор институт",
                    "национальный исследовательский",
                    "технический университет",
                    "не предусмотреть",
                    "фонд оценочный средство",
                    "образование и наука",
                ])))
        ]
        self.xmlprocessor.reduce_style()
        self.par_process(par_processors)
        if not update:
            self.xmlprocessor.style_names()
        self.expand_context()

        self.extracted = True

    def expand_context(self):
        context = {}
        for par in self.tree.iterfind("//par"):
            for cf in CONTEXTUAL_FEATURES:
                if cf in par.attrib:
                    context[cf] = par.get(cf)
                    # del par.attrib[cf]
                if cf in context:
                    par.set("contextual-" + cf, context[cf])
            if len(context) == 0:
                par.set("contextual-no-context", "1")

    def update(self, others=False):
        self.load()
        for par in self.tree.iterfind("//par"):
            attrib = {}
            attrib.update(par.attrib)
            par.attrib.clear()
            a = {k: v
                 for k, v in attrib.items()
                 if k in FIXED_ATTRS or k.startswith("t-")}
            par.attrib.update(a)

        self.extract(update=True)
        if others:
            for o in self.prop_extractors:
                o.update(others=others)

    def learning_params(self, teaching=False):
        self.load()
        param_coding = LearningData()
        target_coding = LearningData()
        self.learn_coding = (param_coding, target_coding, teaching)
        trees = [self] + self.prop_extractors
        for tr in trees:
            for par in tr.tree.iterfind("//par"):
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
        trees = [self] + self.prop_extractors
        for tr in trees:
            for par in tr.tree.iterfind("//par"):
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

    def join_fit(self, prop_extractor):
        self.prop_extractors.append(prop_extractor)

    def fit(self, method="tree", extract=True, debug=False):
        """Prepare parameters for fitting and make a fit.
        """
        des_tree = USE_TREE
        for tr in [self] + self.prop_extractors:
            #print("+++",tr.filename)
            tr.extract()
            #print("---",tr.filename)
        if self.learn_coding is None:
            self.learning_params(teaching=True)
        x, y = self.prepare_params(teaching=True)

        # print(x, y)

        # clf = svm.SVC()
        # m = clf.fit(x, y)
        # clf = GaussianNB()
        # m = clf.fit(x,y)

        param_coding, target_coding, _ = self.learn_coding
        if debug:
            print("Features: -----------------------")
            print(param_coding)
            print("Target features: ----------------")
            print(target_coding)

        models = []
        for i in range(y.shape[1]):
            if des_tree:
                clf = tree.DecisionTreeClassifier()
            else:
                clf = GaussianNB()
            _y = y[:, i]
            m = clf.fit(x, _y)
            models.append(m)
            if des_tree:
                fnexport = self.filename + "-{}.dot".format(i)
                tree.export_graphviz(
                    clf,
                    out_file=open(fnexport, "w"),
                    feature_names=param_coding.source_coding(),
                    class_names=target_coding.target_coding(),
                    # filled=True,
                    # rounded=True,
                special_characters=True)
        self.fit_model = models
        return self.fit_model

    def predict(self, rows=None, par=None, extractor=None):
        """Apply learning models to a rows of encoded values or
        to a paragraph or to a xml tree adding the atttributes
        from fitting.
        """
        if rows is not None:
            models = self.fit_model
            y = np.zeros(shape=(rows.shape[0], len(models)), dtype=float)
            for i, m in enumerate(models):
                _y = m.predict(rows)
                y[:, i] = _y
            return y
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
