from pdfminer.utils import bbox2str
import re

def isclose(a, b, abs_tol=0.0, rel_tol=1e-09):
    # rel_tol is a relative tolerance, it is multiplied by the greater of the magnitudes of the two arguments; as the values get larger, so does the allowed difference between them while still considering them equal.
    # abs_tol is an absolute tolerance that is applied as-is in all cases. If the difference is less than either of those tolerances, the values are considered equal.
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

class BoxItem(object):
    def __init__(self, bbox, name, font_size=0, id=0):
        (x0, y0, x1, y1) = bbox
        self.bbox = bbox
        self.name = name
        self.font_size = font_size
        self.id = id

        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.mid_x = (self.x0 + self.x1) / 2
        self.mid_y = (self.y0 + self.y1) / 2
        self.width = self.x1 - self.x0
        self.height = self.y1 - self.y0
        self.dig_width = 0

    def __repr__(self):
        return ("<%s '%s' (%s w=%.0f h=%.0f dw(%d)>" %
                (self.__class__.__name__,
                 self.name, bbox2str(self.bbox), self.width, self.height, self.dig_width))
    #
    # def digitalize(self, step, margin):
    #     step_w, step_h = step
    #     margin_w, margin_h = margin
    #
    #     if step_w:
    #         dig_w = int((self.width + margin_w * step_w) // step_w)
    #
    #     if step_h:
    #         dig_h = int((self.height + margin_h * step_h) // step_h)
    #
    #     self.dig_w = dig_w
    #     self.dig_h = dig_h
    #
    #     return dig_w, dig_h

    # def split(self, dig_w, dig_h):
    #     if dig_w == 1 and dig_h == 1:   #Not need split
    #         return self
    #
    #     (x0, y0 , x1, y1) = self.bbox
    #     step_x = self.width / dig_w
    #     step_y = self.height / dig_h
    #
    #     result = []
    #     for i in range(dig_w):
    #         x0 = self.x0 + step_x * i
    #         x1 = x0 + step_x
    #         for j in range(dig_h):
    #             y0 = self.y0 + step_y * j
    #             y1 = y0 + step_y
    #             elem_new = self.__class__((x0, y0, x1, y1), self.name, self.font_size)
    #             elem_new.dig_w = self.dig_w
    #             result.append(elem_new)
    #
    #     return result

    def set_dig_w(self, dig):
        self.dig_width = dig

    def v_split(self, height):
        (x0, y0 , x1, y1) = self.bbox
        dig_w = self.dig_width

        bbox_new = (x0, y0, x1, y1 - height)
        elem_new = self.__class__(bbox_new, self.name, self.font_size, self.id + 1)
        #elem_new.set_dig_w(dig_w)

        #reset value
        bbox = (x0, y1 - height, x1, y1)
        self.__init__(bbox, self.name, self.font_size)
        self.set_dig_w(dig_w)

        return elem_new

    # def v_split(self, splited_h):
    #     (x0, y0 , x1, y1) = self.bbox
    #     step_y = self.height / splited_h
    #
    #     result = []
    #     dig_w, dig_h= self.digital
    #     for j in range(splited_h):
    #         y1 = self.y1 - step_y * j
    #         y0 = y1 - step_y
    #         elem_new = self.__class__((x0, y0, x1, y1), "%s (%d)" % (self.name, j), self.font_size)
    #         elem_new.set_dig((dig_w, 1))
    #         result.append(elem_new)
    #
    #     return result

class TableElement(object):
    def __init__(self, index, laparams):
        self.index = index  #table index
        self.name = None
        self.rows = []  # store final processed table data
        #self._row_curr = 0
        self._cache = []    #temp varible in processing, store 1 line elems
        self._raw_cache = [] #temp varible in processing, store whole comibned elems
        self._extras = []   #temp varible in processing, store splited elems
        self._comments = [] # store comments with is not in bbox
        self.outline_bbox = ()    #store table rectangle outline
        self.laparams = laparams

    def __repr__(self):
        return ('<%s(%d)>' %
                (self.__class__.__name__,
                 len(self.rows)))

    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, key):
        return self.rows[key]

    def __len__(self):
        return len(self.rows)

    def put_raw_cache(self, item, border_bbox):
        x0, y0, x1, y1 = border_bbox
        text = item.get_text().strip()
        for el in self._raw_cache:
            if isclose(el.x0, x0) and isclose(el.y0, y0) and \
                    isclose(el.x1, x1) and isclose(el.y1, y1):
                if el.name != text:
                    el.name = ' '.join((el.name, text))    #combine the text in same box
                return

        elem = BoxItem(border_bbox, text)
        if not self._raw_cache:
            self.outline_bbox = border_bbox
        else:
            x0 = min(x0, self.outline_bbox[0])
            y0 = min(y0, self.outline_bbox[1])
            x1 = max(x1, self.outline_bbox[2])
            y1 = max(y1, self.outline_bbox[3])
            self.outline_bbox = (x0, y0, x1, y1)

        self._raw_cache.append(elem)

    def get_outline(self):
        if self._raw_cache:
            return self.outline_bbox

    def cache_empty(self):
        return not self._cache

    def cache_data(self, idx):
        if idx < len(self._cache):
            return self._cache[idx]

    def first_cache_elem(self):
        return self.cache_data(0)

    def put_cache(self, elem):
        self._cache.append(elem)

    def save_cache(self):
        for elem in self._cache:
            self.digitalize(elem)

        self._cache.sort(key=lambda d: d.x0)
        self.rows.append(self._cache)
        self._cache = []
        #self._row_curr += 1

    def is_row_end(self, elem_new):
        margin_w, margin_h = self.laparams.table_border_margin
        elem_cache_first = self.first_cache_elem()
        if elem_new.y1 < elem_cache_first.y0 + margin_h * elem_cache_first.height:  # new line compared to row first element
            return True
        else:
            return False

    def is_table_end(self, item_new):
        margin_w, margin_h = self.laparams.table_border_margin
        # elem_cache_first = self.first_cache_elem()
        # first_row_elems = self.i_row(0)
        # if item_new.y1 < elem_cache_first.y0 + margin_h * elem_cache_first.height and \
        #         item_new.x1 > first_row_elems[0].x0 - margin_w * first_row_elems[0].width and \
        #         item_new.x0 < first_row_elems[-1].x1 + margin_w * first_row_elems[-1].width:
        #     return True
        # else:
        #     return False
        outline_bbox = self.get_outline()
        if outline_bbox:
            x0, y0, x1, y1 = outline_bbox
            height = item_new.y1 - item_new.y0
            width = item_new.x1 - item_new.x0
            if item_new.y1 < y0 + margin_h * height and \
                    item_new.x1 > x0 - margin_w * width and \
                    item_new.x0 < x1 + margin_w * width:
                return True

        return False

    def empty(self):
        return not self.rows

    def i_row(self, idx):
        if idx < len(self.rows):
            return self.rows[idx]

    def digitalize(self, elem):
        if self.empty():
            dig_w = 1
        else:
            dig_w = 0
            for el in self.i_row(0):
                if el.mid_x > elem.x0:
                    if el.mid_x < elem.x1:
                        dig_w += 1
                    else:
                        break

        elem.set_dig_w(dig_w)

    def put_extra(self, data):
        if isinstance(data, (list, tuple)):
            self._extras.extend(data)
        else:
            self._extras.append(data)

    def handle_extra(self, elem):
        if self._extras:
            extras_new = []
            for el in self._extras: #insert extra elem to handle
                if el.x0 < elem.x0 and \
                        elem.mid_y > el.y0 and elem.mid_y < el.y1:
                    self.put_cache(el)
                else:
                    extras_new.append(el)
            self._extras = extras_new

    def merge_extra(self):
        for s_elem in self._extras:
            for row_elems in self.rows:
                # if s_elem.y0 > row_data[0].y0 - margin_h.row_data[0].height and \
                #                 s_elem.y1 < row_data[0].y1 + margin_h.row_data[0].height:
                row_elem_first = row_elems[0]
                if s_elem.mid_y > row_elem_first.y0 and s_elem.mid_y < row_elem_first.y1:
                    row_elems.append(s_elem)
                    sorted(row_elems, key=lambda d: d.x0)
                    break

    def put_comment(self, text):
        self._comments.append(text)

    def extend(self, other):
        # Fixme: it's simple copy, not change the bbox relatvie position value
        for i, row in enumerate(self):  # removed duplicated title
            row_new = other.i_row(i)
            row_len = len(row)
            for j in range(row_len):
                if row[j].name != row_new[j].name:
                    break

            if j + 1 != row_len:
                break

        self.rows.extend(other[i:])

    def done(self):
        for elem in self._raw_cache:
            self.feed_t(elem)

        if self._cache:
            self.save_cache()

        self.merge_extra()
        if len(self._comments) > 1:
            self.name = self._comments[1]

    #def parse_table(self, items, item_id, curver_id, word_margin, line_margin):
    def feed_t(self, elem):
        def get_pos_elem(elem_table, x, y=None):
            x_matched, y_matched = (False, False)
            for elem in elem_table:
                if x:
                    if x >= elem.x0 and x <= elem.x1:
                        x_matched = True

                if y:
                    if y >= elem.y0 and y <= elem.y1:
                        y_matched = True

                if (x_matched or not x) and (y_matched or not y):
                    return elem

        elem_cache_first = self.first_cache_elem()
        # if not elem_cache_first:
        #     self.put_cache(elem)
        #     return

        if elem_cache_first is not None:
            if self.is_row_end(elem):
                self.save_cache()
                #self.put_cache(elem)
            else:
                # if self.empty():  #assume first row is stand element width
                #     self.put_cache(elem)
                # else:

                margin_w, margin_h = self.laparams.table_border_margin
                #self.digitalize(elem)

                if isclose(elem_cache_first.height, elem.height, 0, margin_h):
                    pass
                elif elem_cache_first.height < elem.height:
                    elem_new = elem.v_split(elem_cache_first.height)
                    self.put_extra(elem_new)
                else:
                    result = []
                    for el in self._cache:
                        elem_new = el.v_split(elem.height)
                        result.append(elem_new)
                    self.put_extra(result)

                #self.put_cache(elem)

        self.handle_extra(elem)
        self.put_cache(elem)

class CommentElement(object):
    def __init__(self, item, parent=None):
        self.item = item
        self.parent = parent
        self.children = []
        # self.status = None

    def __repr__(self):
        return ('<%s(%d) %s>:' %
                (self.__class__.__name__,
                 len(self.children), str(self.item)))

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, key):
        return self.children[key]

    def __len__(self):
        return len(self.children)

    def left(self):
        return self.item.x0

    def top(self):
        return self.item.y1

    # def set_parent(self, elem):
    #     self.parent = elem

    def push_item(self, item):
        elem = self.__class__(item, self)
        # self.building_child.append(elem)
        self.children.append(elem)
        return elem

    def done(self):
        if self.building_child:
            self.children.append(self.building_child)
            self.building_child = []

    def feed_c(self, item):
        if not self.children and not self.parent:
            return self.push_item(item)
        else:
            #for elem in reversed(self.children):
            if self.children:
                elem = self.children[-1]
                if isclose(item.x0, elem.left(), 1):
                    return self.push_item(item)
                elif item.x0 < elem.left():
                    pass
                else:
                    # result = None
                    # if elem.children:
                    #     result = elem.feed(item)
                    #     if not result:
                    #         return elem.push_item(item)
                    # else:
                    #     return elem.push_item(item)
                    #
                    # return result
                    if elem.children:
                        result = elem.feed_c(item)
                        if result is not None:
                            return result

                    return elem.push_item(item)

            if not self.parent:
                print("Found a new level 1 item:", item)
                return elem.push_item(item)

class IndentElement(object):
    PATTERN_TABLE = r'(Table) (\d+)-(\d+)\.'
    def __init__(self, item, laparams):
        self.item = item
        self.laparams = laparams
        self.comments = CommentElement(BoxItem(item.bbox, item.pageid))
        self._table = None
        self.tables = {}
        self.pat_tab = re.compile(self.PATTERN_TABLE)

    def __repr__(self):
        return ('<%s %s:%s %s>' %
                (self.__class__.__name__, str(self.item),
                    str(self.comments), str(self.tables)))

    @staticmethod
    def create_root_element(item, laparams):
        return IndentElement(item, laparams)

    @staticmethod
    def search_border(item, curves, laparams):
        def get_closer(item, curve0, curve1, attr_name):
            a = getattr(item, attr_name)
            x0 = getattr(curve0, attr_name)
            x1 = getattr(curve1, attr_name)

            if abs(a - x0) > abs(a - x1):
                return curve1
            else:
                return curve0

        margin_w, margin_h = laparams.table_border_margin
        top, bottom, left, right = (None, None, None, None)
        for curve in curves:
            if curve.width * laparams.curver_line_ratio > curve.height:
                mid_x = (item.x0 + item.x1) // 2
                if mid_x >= curve.x0 and mid_x <= curve.x1:
                    margin = item.height * margin_h
                    if item.y1 <= curve.y1 + margin:
                        #     ------
                        #       ab
                        # print("Top:",curve, item)
                        if not top:
                            top = curve
                        else:
                            top = get_closer(item, top, curve, 'y1')
                    elif item.y0 >= curve.y0 - margin:
                        #       ab
                        #     ------
                        # print("Bottom:", curve, item)
                        if not bottom:
                            bottom = curve
                        else:
                            bottom = get_closer(item, bottom, curve, 'y0')
                    else:
                        print("Crossed curve in y direction:", curve, item, margin)
            elif curve.height * laparams.curver_line_ratio > curve.width:
                mid_y = (item.y0 + item.y1) // 2
                if mid_y >= curve.y0 and mid_y <= curve.y1:
                    margin = item.width * margin_w
                    if item.x0 > curve.x0 - margin:
                        #   |
                        #   |   ab
                        #   |
                        # print("Left:", curve, item)
                        if not left:
                            left = curve
                        else:
                            left = get_closer(item, left, curve, 'x1')
                    elif item.x1 < curve.x1 + margin:
                        #       |
                        #   ab  |
                        #       |
                        # print("Right:", curve, item)
                        if not right:
                            right = curve
                        else:
                            right = get_closer(item, right, curve, 'x0')
                    else:
                        print("Crossed curve in x direction:", curve, item, margin)
            else:
                print("Not curve line, discard:", curve)

        if all((top, bottom, left, right)):
            return (left.x0, bottom.y0, right.x1, top.y1)

    def probe_table(self, item, curves):
        text = item.get_text().strip()
        if self._table is None:
            result = self.pat_tab.match(text)
            if result is not None:
                self._table = TableElement(result.groups(), self.laparams)
        else:
            if self._table is not None:
                bbox = self.search_border(item, curves, self.laparams)
                if not bbox:
                    if self._table.is_table_end(item):
                        self.complete_table()
                    else:
                        self._table.put_comment(text)
                else:
                    self._table.put_raw_cache(item, bbox)
                    return bbox

    def complete_table(self):
        if self._table is not None:
            self._table.done()
            if len(self._table):
                idx = self._table.index
                if not idx in self.tables:
                    self.tables[idx] = self._table
                else:
                    self.tables[idx].extend(self._table)
            self._table = None

    def complete(self):
        self.complete_table()

    def feed(self, item, curves):
        result = self.probe_table(item, curves)
        if result is None:
            self.comments.feed_c(item)

    # def feed2(self, item):
    #     if not self.building_child:
    #         self.push_item(item)
    #         return self
    #
    #     header = self.building_child[0]
    #     if item.y1 == header.top():
    #         self.push_item(item)
    #     else:
    #         sibing = None
    #         for i, elem in enumerate(self.building_child):
    #             if item.x0 < elem.left():
    #                 break
    #             elif item.x0 == elem.left():
    #                 if i == 0:
    #                     sibing = None
    #                 break
    #             else:
    #                 sibing = elem
    #
    #         if sibing:
    #             return sibing.feed(item)
    #         else:
    #             if item.x0 <= self.left():
    #                 if self.parent:
    #                     self.done()
    #                     return self.parent.feed(item)
    #                 else:
    #                     print("Drop un-decided item:", item)
    #             else:
    #                 self.push_item(item)
    #
    #     return self