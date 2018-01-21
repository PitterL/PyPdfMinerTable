import re
import json

from pdfminer.layout import LTPage
from protocol.indparser import BoxItem, IndentElement
from pdfminer.utils import bbox2str

class PStatus(object):

    def __init__(self, chapter_types):
        self.chapters = chapter_types
        # self.sections = []
        self.curr_chap = 0
        # self.curr_sec = 0

    # def get(self):
    #     if self.curr_chap < len(self.chapters):
    #         return self.chapters[self.curr_chap]

    def at(self, chapter=None):
        if self.curr_chap < len(self.chapters):
            if chapter:
                return self.chapters[self.curr_chap] == chapter
            else:
                return self.chapters[self.curr_chap]

    def done(self):
        if self.curr_chap < len(self.chapters):
            self.curr_chap += 1

    # def add_sec(self, section):
    #     self.sections.append(section)
    #
    # def at_sec(self, section):
    #     return self.sections[self.curr_sec] == section
    #
    # def done_sec(self):
    #     if self.curr_sec < len(self.sections):
    #         self.curr_sec += 1

# class RegConfigTable():
#     class BoxElement(object):
#         def __init__(self, bbox, name, word_margin=None, line_margin=None):
#             (x0, y0, x1, y1) = bbox
#             self.bbox = bbox
#             self.name = name
#             self.word_margin = word_margin
#             self.line_margin = line_margin
#
#             self.x0 = x0
#             self.x1 = x1
#             self.y0 = y0
#             self.y1 = y1
#             self.mid_x = (self.x0 + self.x1) / 2
#             self.mid_y = (self.y0,+ self.y1) / 2
#             self.width = self.x1 - self.x0
#             self.height = self.y1 - self.y0
#
#             self.dig_width = 1
#             self.dig_height = 1
#
#         def set_row(self, row_id):
#             self.row_id = row_id
#
#         def digitalize(self, step_w, step_h):
#             if step_w:
#                 self.dig_width = (self.width + (1 + word_margin) * step_w) // step_w
#
#             if step_h:
#                 self.dig_height = (self.height + (1 + line_margin) * step_h) // step_h
#
#             return self.dig_width, self.dig_height
#
#         def split(self, dig_w, dig_h):
#             if dig_w < 1 and dig_h < 1:
#                 return self
#
#             (x0, y0 , x1, y1) = self.bbox
#             step_x = self.width / dig_w
#             step_y = self.height / dig_h
#
#             result = []
#             for i in range(dig_w):
#                 x0 = self.x0 + step_x * i
#                 x1 = x0 + step_x
#                 for j in range(dig_h):
#                     y0 = self.y0 + step_y * j
#                     y1 = y0 + step_y
#                     elem_new = self.__class__((x0, y0, x1, y1), self.name, self.word_margin, self.line_margin)
#                     result.append(elem_new)
#
#             return result
#
#     TABLE_TITLE_NAME = ('Byte', 'Field', 'Bit 7', 'Bit 6', 'Bit 5', 'Bit 4', 'Bit 3', 'Bit 2', 'Bit 1', 'Bit 0')
#     (ELEM_ID, ELEM_NAME) = range(2)
#     (TABLE_TITLE, ) = range(1)
#
#     ROW_TYPE = ('Title', 'Data')
#     def __init__(self, reg_id):
#         self.reg_id = reg_id
#         #self.status = ParseStep(steps)
#         self.title = []
#         self.table = []
#         self.table_comment = []
#         self.row_data = []
#
#     def get_named_elem(self, name):
#         for row_data in self.table:
#             for elem in row_data:
#                 if elem.name == name:
#                     return elem
#
#
#         # attr_name = ('x1', 'y1', 'x0', 'y0')    # inner line
#         # bbox = []
#         # for i, border in enumerate(rect):
#         #     if border:
#         #         bbox.append(getattr(border, attr_name[i]))
#         #     else:
#         #         bbox.append(item.bbox[i])
#         #
#         # return bbox
#         if not all(borders):
#             return None
#
#         return (top.x1, bottom.y1, left.x0, right.y0)
#
#     def parse_table(self, items, item_id, curver_id, word_margin, line_margin):
#         def get_pos_elem(elem_table, x, y=None):
#             x_matched, y_matched = (False, False)
#             for elem in elem_table:
#                 if x:
#                     if x >= elem.x0 and x <= elem.x1:
#                         x_matched = True
#
#                 if y:
#                     if y >= elem.y0 and y <= elem.y1:
#                         y_matched = True
#
#                 if (x_matched or not x) and (y_matched or not y):
#                     return elem
#
#         row_data = []
#         extra_data = []
#         curr_row_id = 0
#
#         for i in range(item_id, curver_id):
#             child = items[i]
#             if not hasattr('get_text', child):
#                 break
#
#             text = child.get_text().strip()
#             bbox = self.search_border(items, item_id, curver_id)
#
#             if bbox:
#                 elem = self.BoxElement(bbox, text, word_margin, line_margin)
#                 if not row_data:
#                     row_data.append(elem)
#                 else:
#                     elem_row_first = row_data[0]
#                     if elem.y1 <  elem_row_first.y0 + line_margin *  elem_row_first.height: # new line compared to row first element
#                         self.table.append(row_data)
#                         row_data = []
#                         curr_row_id += 1
#
#                     elem.set_row(curr_row_id)
#                     if row_data:
#                         step_x = elem.width
#                         if self.table:  #assume first row is stand element width
#                             col_ref = get_pos_elem(self.table[TABLE_TITLE], elem.mid_x)
#                             if col_ref:
#                                 step_x = col_ref.width
#
#                         row_ref = row_data[ELEM_ID] #assume first element is stand element height
#                         step_y = row_ref.height
#
#                         dig_w, dig_h = elem.digitalize(step_x, step_y)
#                         result = elem.split(1, dig_h)
#                         if elem is result:  # not splitted
#                             row_data.append(elem)
#                         else:
#                             extra_data.extend[result]
#                     else:
#                         row_data.append(elem)
#             else:
#                 if row_data:
#                     elem_name = row_data[self.ELEM_NAME]
#                     if text == elem_name:
#                         break
#                     else:
#                         self.table_comment.append(text)
#                 else:
#                     print("Skip useless item:", child)
#
#         for s_elem in extra_data:
#             for row_data in self.table:
#                 if s_elem.y0 > row_data[0].y0 - line_margin.row_data[0].height and \
#                     s_elem_y1 < row_data[0].y1 + line_margin.row_data[0].height:
#                     row_data.append(s_elem)
#                     sorted(row_data, key = lambda d: d.x0)
#                     break
#
#     def parse_comment(self, item_id, curver_id):
#         for i in range(item_id, curver_id):
#             child = items[i]
#             if not hasattr('get_text', child):
#                 break
#
#             text = child.get_text().strip()
#             elem = self.get_named_elem(text)
#             if elem:
#                 pass

#section index info
class ProtocolIndex(object):
    SECTION_COL_NAME = ('Chapter', 'Section', 'Reg ID', 'Reg Name', 'Reg Desc', 'Page Start')
    (IDX_CHAPTER, IDX_SECTION, IDX_REG_ID, IDX_REG_NAME, IDX_REG_DESC, IDX_PAGE_ST) = range(6)

    def __init__(self):
        self.chapters = {}
        self.sections = []
        # self.objects = {}

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
        print(reg_elem)

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
        print(self.reg_index.chapters)
        print(self.reg_content)
        a = json.dumps(list(self.reg_index))
        #json.dumps(list(self.reg_index))
        #json.dumps( for t in self.reg_content.tables)