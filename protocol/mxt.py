import re
import json

from pdfminer.layout import LTPage
from protocol.indparser import BoxItem, IndentElement
from pdfminer.utils import bbox2str

class PStatus(object):

    def __init__(self, chapter_types):
        self.chapters = chapter_types
        self.curr_chap = 0

    def at(self, chapter=None):
        if self.curr_chap < len(self.chapters):
            if chapter:
                return self.chapters[self.curr_chap] == chapter
            else:
                return self.chapters[self.curr_chap]

    def done(self):
        if self.curr_chap < len(self.chapters):
            self.curr_chap += 1
class ProtocolIndex(object):
    # section index info
    SECTION_COL_NAME = ('Chapter', 'Section', 'Reg ID', 'Reg Name', 'Reg Desc', 'Page Start')
    (IDX_CHAPTER, IDX_SECTION, IDX_REG_ID, IDX_REG_NAME, IDX_REG_DESC, IDX_PAGE_ST) = range(6)

    def __init__(self):
        self.chapters = {}
        self.sections = []

    def __repr__(self):
        return "Protocal Index:\n\tChapter: %s:\n\tSection:%s" % (str(self.chapters), str(self.sections))

    def __iter__(self):
        return iter(self.sections)

    def __getitem__(self, key):
        return self.sections[key]

    def __len__(self):
        return len(self.sections)

    def add_chapter(self, chapter_no, name):
        self.chapters[chapter_no] = name

    def add_section(self, chapter_no, section_no, name, page):
        def parse_name(name):
            pat_o = re.compile("([\w ]+)\((\w+)\)")
            pat_i = re.compile("\sT(\d+)\s")
            # 'Diagnostic Debug T37 (DEBUG_DIAGNOSTIC_T37) -> ('Diagnostic Debug T37 ', 'DEBUG_DIAGNOSTIC_T37')
            result_o = pat_o.match(name)
            if result_o:
                obj_desc = result_o.group(1)
                obj_name = result_o.group(2)
                #'Diagnostic Debug T37 ' -> '37'
                result_i = pat_i.search(obj_desc)
                if result_i:
                    obj_id = int(result_i.group(1))
                    return (obj_id, obj_name, obj_desc)

        info = parse_name(name)
        if not info:
            info = (None, None, name)
        self.sections.append([chapter_no, section_no, *info, page])

    def add_content(self, index_name, name, pageno):
        result = index_name.split('.')
        if len(result) == 2:
            self.add_section(result[0].strip(), result[1].strip(), name.strip(), int(pageno.strip()))
        else:
            self.add_chapter(index_name.strip(), name.strip())

    def pageno_to_secinfo(self, pageno):
        result = None
        for sec in self.sections:
            page_st = sec[self.IDX_PAGE_ST]
            if pageno >= page_st:
                result = sec
            else:
                break

        return result

class MxtProtocol(object):
    PAGE_TYPE = ('cover', 'index', 'chapter')

    def __init__(self, laparams, steps=PAGE_TYPE, range=(2,4)):
        self.laparams  = laparams
        self.status = PStatus(steps)
        self.reg_index = ProtocolIndex()
        self.reg_content = {}
        self.name = None
        self.version = None

    def parse_protocol_cover(self, items):
        for i, child in enumerate(items):
            if hasattr(child, 'get_text'):
                break

        if i < len(items) - 1:
            self.name = items[i].get_text().strip()
            self.version = items[i + 1].get_text().strip()

        self.status.done()

    def parse_protocol_index(self, items):
        pat_sp = re.compile(" ?\. ")
        pat_cpt = re.compile("\w\.\d+")
        start_words = ("Table of Contents",)
        end_words = ('Associated Documents', 'Known Issues', 'Revision History')

        id_item = None
        for child in items:
            if not hasattr(child, 'get_text'):
                break

            text = child.get_text()
            result = pat_sp.split(text)
            words = list(filter(None, result))
            if len(words) == 3:
                chapter, name, page = words
                self.reg_index.add_content(chapter, name, page)
            elif len(words) == 2:
                if id_item:
                    if child.y0 >= id_item.y0 and child.y0 <= id_item.y1 or \
                                            child.y1 >= id_item.y0 and child.y1 <= id_item.y1:
                        chapter = id_item.get_text()
                        name, page =  words
                        self.reg_index.add_content(chapter, name, page)
                else:
                    name, page = words
                    if name in start_words:
                        print("Found Book Index:", name, page)

                    if name in end_words:
                        self.status.done()
                        #print(self.reg_index)
                        break
            else:
                if pat_cpt.match(text):
                    id_item = child
                    continue
            id_item = None

    def parse_protocol_chapter(self, items):
        def get_curve_obj_st(items):
            for i, child in enumerate(items):
                if not hasattr(child, 'get_text'):
                    break
            return i

        def get_curve_index(items):
            for i, child in enumerate(reversed(items)):
                if hasattr(child, 'get_text'):
                    break

            if i > 0:
                return len(items) - i

        page_no = items.pageid
        sec_info = self.reg_index.pageno_to_secinfo(page_no)

        if not sec_info:
            return

        cid = sec_info[ProtocolIndex.IDX_REG_ID]
        if not cid:
              cid = sec_info[ProtocolIndex.IDX_REG_DESC]

        if cid not in self.reg_content:
            reg_elem = IndentElement.create_root_element(items, self.laparams)
            self.reg_content[cid] = reg_elem
        else:
            reg_elem = self.reg_content[cid]

        curve_index = get_curve_index(items)
        curves = items[curve_index:]
        ratio_h, ratio_f = self.laparams.page_header_footer
        header_pos = items.height *  (1 - ratio_h)
        footer_pos = items.height * ratio_f
        for i in range(curve_index):
            item = items[i]
            if item.y0 > header_pos:
                continue

            if item.y0 < footer_pos:
                break

            reg_elem.feed(item, curves)

        reg_elem.complete()
        #print(reg_elem)

    def parse(self, page_item):
        if not isinstance(page_item, LTPage):
            print("Unhandled page_item type:", page_item)
            return

        status = self.status.at()
        fn_name = "parse_protocol_" + status
        fn = getattr(self, fn_name)
        if fn:
            fn(page_item)
        else:
            print("Unhandled status:", self.status)

    def done(self):
        print(self.name)
        print(self.version)
        print("chapters")
        print(self.reg_index.chapters)
        print("sections")
        print(self.reg_index.SECTION_COL_NAME)
        print(self.reg_index.sections)

        result = {}
        for k0, v0 in self.reg_content.items():
            # print(k0)
            # print("comments")
            # print(v0.comments)
            # print("tables")
            # print(v0.tables)
            for k1, v1 in v0.tables.items():
                print(k1, v1.name)
                if v1.name.startswith("Configuration for") or \
                    v1.name.startswith("Message Data for"):
                    print(k1)
                    print(v1.name)
                    content = [[(elem.name, elem.dig_width) for elem in row] for row in v1.rows]
                    print(content)
                    result[v1.name] = content

        if result:
            with open('../samples/test/db.txt', 'w') as outfile:
                json.dump(result, outfile)

        #json.dumps(list(self.reg_index))
        #json.dumps(self.reg_content)
        #json.dumps(list(self.reg_index))
        #json.dumps( for t in self.reg_content.tables)