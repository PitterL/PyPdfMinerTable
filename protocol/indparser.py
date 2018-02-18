from pdfminer.utils import bbox2str
import re

def isclose(a, b, abs_tol=0.0, rel_tol=1e-09):
    # rel_tol is a relative tolerance, it is multiplied by the greater of the magnitudes of the two arguments; as the values get larger, so does the allowed difference between them while still considering them equal.
    # abs_tol is an absolute tolerance that is applied as-is in all cases. If the difference is less than either of those tolerances, the values are considered equal.
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

class BoxItem(object):
    def __init__(self, bbox, name, font_size=0, id=None):
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

    def set_dig_w(self, dig):
        self.dig_width = dig

    # def split_name(self, name):
    #     pat = re.compile("(\d)\s*[–-]\s*(\d)")
    #     result = pat.match(name)
    #     if result:
    #         st = int(result.group(1))
    #         end = int(result.group(2))
    #
    #         st_new = st + 1
    #         if st_new == end:   # name '3-4' -> '3', '4'
    #             sp_name = str(st), str(st_new)
    #         else:   # name: '3 - 6' -> '3', '4 - 6'
    #             sp_name = str(st), "%d - %d" % (st_new, end)
    #     else:
    #         suffix_c = name[-1]
    #         if suffix_c >= '0' and suffix_c <= '9': #name 'DATATYPE 1' -> 'DATATYPE 1', 'DATATYPE 2'
    #             new_suffix_c = chr(ord(suffix_c) + 1)
    #             sp_name = name, name[:-1] + new_suffix_c
    #         else:   #name 'DATATYPE' -> 'DATATYPE 0', 'DATATYPE 1'
    #             sp_name = name + ' 0', name + ' 1'
    #
    #     return sp_name

    def sequence_name(self):
        seq = self.id
        if seq is None:
            return

        pat = re.compile("(\d)\s*[–-]\s*(\d)")
        result = pat.match(self.name)
        if result:
            st = int(result.group(1))
            end = int(result.group(2))

            # st_new = st + 1
            # if st_new == end:   # name '3-4' -> '3', '4'
            #     sp_name = str(st), str(st_new)
            # else:   # name: '3 - 6' -> '3', '4 - 6'
            #     sp_name = str(st), "%d - %d" % (st_new, end)
            assert st + seq <= end
            sp_name = str(st + seq)
        else:
            # suffix_c = name[-1]
            # if suffix_c >= '0' and suffix_c <= '9': #name 'DATATYPE 1' -> 'DATATYPE 1', 'DATATYPE 2'
            #     new_suffix_c = chr(ord(suffix_c) + 1)
            #     sp_name = name, name[:-1] + new_suffix_c
            # else:   #name 'DATATYPE' -> 'DATATYPE 0', 'DATATYPE 1'
            #     sp_name = name + ' 0', name + ' 1'
            sp_name = self.name + " " + str(seq)

        self.name = sp_name

    # def v_split_old(self, height):
    #     (x0, y0 , x1, y1) = self.bbox
    #     dig_w = self.dig_width
    #
    #     bbox_new = (x0, y0, x1, y1 - height)
    #     name, name_new = self.split_name(self.name)
    #     elem_new = self.__class__(bbox_new, name_new, self.font_size, self.id + 1)
    #     #elem_new.set_dig_w(dig_w)
    #
    #     #reset value
    #     bbox = (x0, y1 - height, x1, y1)
    #     self.__init__(bbox, name, self.font_size)
    #     self.set_dig_w(dig_w)
    #
    #     return elem_new

    def v_split(self, elem, margin_h):
        (x0, y0 , x1, y1) = self.bbox
        #dig_w = self.dig_width
        extra = []
        id = self.id
        if id is None:
            id = 0 # Fixme: there will be id overlap is middle element should be split again.
        seq = 0

        """
        self is higher than target
                    -----           (x1, y1)
                    |   |   
                    |   |     -----
                    |   |     |   |
           (x0, y0) -----     -----
        
                     self      elem
        """
        abs_tol = margin_h * elem.height
        if not isclose(elem.y1, y1, abs_tol) and elem.y1 < y1:
            bbox_new = (x0, elem.y1, x1, y1)
            elem_new = self.__class__(bbox_new, self.name, self.font_size, id)
            seq += 1
            extra.append(elem_new)


        """
        self is lower than target
                    -----     -----  (x1, y1)
                    |   |     |   |
                    |   |     -----
                    |   |
            (x0,y0) -----  
                     self      elem
        """
        if not isclose(elem.y0, y0, abs_tol) and elem.y0 > y0:
            bbox_new = (x0, y0, x1, elem.y0)
            elem_new = self.__class__(bbox_new, self.name, self.font_size, id + seq + 1)
            extra.append(elem_new)

        #reset value
        bbox = (x0, elem.y0, x1, elem.y1)
        self.__init__(bbox, self.name, self.font_size, id + seq)
        #self.set_dig_w(dig_w)

        print(self.__class__.__name__, 'v_split:', 'self', self, 'extra', extra)
        assert extra
        return extra

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

    def cached_first(self):
        return len(self._cache) == 1

    def put_cache(self, elem):
        self._cache.append(elem)

    def save_cache(self):
        # for elem in self._cache:
        #     self.digitalize(elem)

        self._cache.sort(key=lambda d: d.x0)    #Fixme: no need sort each time, only with splitted line
        self.rows.append(self._cache)
        self._cache = []
        #self._row_curr += 1

    def empty(self):
        return not self.rows

    def i_row(self, idx):
        if idx < len(self.rows):
            return self.rows[idx]

    def is_row_end(self, elem_new):
        margin_w, margin_h = self.laparams.table_border_margin
        elem_cache_first = self.first_cache_elem()
        if elem_new.y1 < elem_cache_first.y0 + margin_h * elem_cache_first.height:  # new line compared to row first element
            return True
        else:
            return False

    def is_table_end(self, item_new):
        margin_w, margin_h = self.laparams.table_border_margin
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

    def split_elem(self, cache, elem, margin_h):
        elem_cache_first = cache[0]
        if isclose(elem_cache_first.height, elem.height, 0, margin_h):
            return (elem,None)
        elif elem_cache_first.height < elem.height:
            elems_new = elem.v_split(elem_cache_first, margin_h)
            return (elem, elems_new)
        else:
            result = []
            for el in cache:
                elems_new = el.v_split(elem, margin_h)
                result.extend(elems_new)
            return (elem, result if result else None)

    def put_elem(self, row_elems, elem_new):
        assert elem_new
        row_elems.append(elem_new)
        row_elems.sort(key=lambda d: d.x0)
        #print(self.__class__.__name__, "put_elem", "sorted", row_elems)

    def dump_extras(self):
        #print(self.__class__.__name__, "dump_extras", self._extras)
        extra_dup = self._extras
        self._extras = []
        return extra_dup

    def extras_size(self):
        return len(self._extras)

    def extras_range(self):
        if self.extras_size():
            x0, y0, x1, y1 = self._extras[0].bbox
            for el in self._extras[1:]:
                x0 = min(x0, el.x0)
                y0 = min(y0, el.y0)
                x1 = min(x1, el.x1)
                y1 = min(y1, el.y1)

            return (x0, y0, x1, y1)

    def put_extra(self, data):
        #print(self.__class__.__name__, "put_extra:", type(data), data)
        if data:
            if isinstance(data, (list, tuple)):
                self._extras.extend(data)
            else:
                self._extras.append(data)
        #print(self.__class__.__name__, "put_extra extra:", self._extras)

    # def handle_extra(self, elem):
    #     if self._extras:
    #         extras_dup = self._extras
    #         self._extras = []
    #         for el in extras_dup: #insert extra elem to handle
    #             if el.mid_x < elem.x0 or el.mid_x > elem.x1:    #outside at x axis
    #                 if (el.mid_y > elem.y0 and el.mid_y < elem.y1) or   \
    #                     (elem.mid_y > el.y0 and elem.mid_y < el.y1):  #but in y range
    #                     yield el
    #             else:
    #                 self.put_extra(el)

    def handle_extra(self, row_elems):
        #extras_dup should the copy of self._extras
        extras_dup = self.dump_extras()

        elem = row_elems[0]
        for el in extras_dup: #insert extra elem to handle
            if el.mid_x < elem.x0 or el.mid_x > elem.x1:    #outside at x axis
                if (el.mid_y > elem.y0 and el.mid_y < elem.y1) or   \
                    (elem.mid_y > el.y0 and elem.mid_y < el.y1):  #but in y range
                    _, margin_h = self.laparams.table_border_margin
                    elem_new, extra = self.split_elem(row_elems, el, margin_h)
                    self.put_elem(row_elems, elem_new)
                    if extra:
                        self.put_extra(extra)
                    continue
            self.put_extra(el)

    def merge_extra(self):
        _, margin_h = self.laparams.table_border_margin
        count = len(self.rows)
        for i in range(count):
            for row_elems in self.rows:
                elem = self.handle_extra(row_elems)
                if not self.extras_size():
                    break

            bbox = self.extras_range()
            if not bbox:
                break

            elem_high = self.rows[0][0]
            elem_low = self.rows[-1][-1]
            if bbox[1] > elem_high.mid_y or \
                            bbox[3] < elem_low.mid_y: #above the elem, or below the elem
                print("drop extras data:", self._extras)
                break

        if i + 1 == count:
            print(self.__class__.__name__, "merge_extra", "overflow!")

    def digitalize(self):
        if self.empty():
            return
        else:
            ref_row = self.i_row(0)
            for row in self.rows:
                for elem in row:
                    dig_w = 0
                    for el in ref_row:
                        if el.mid_x > elem.x0:
                            if el.mid_x < elem.x1:
                                dig_w += 1
                            else:
                                break
                    elem.set_dig_w(dig_w)


    def put_comment(self, text):
        self._comments.append(text.strip())

    def i_comment(self, idx):
        if idx < len(self._comments):
            return self._comments[idx]

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

        if elem_cache_first is not None:
            if self.is_row_end(elem):
                self.save_cache()
            else:
                # margin_w, margin_h = self.laparams.table_border_margin
                # if isclose(elem_cache_first.height, elem.height, 0, margin_h):
                #     pass
                # elif elem_cache_first.height < elem.height:
                #     elem_new = elem.v_split(elem_cache_first.height)
                #     self.put_extra(elem_new)
                # else:
                #     result = []
                #     for el in self._cache:
                #         elem_new = el.v_split(elem.height)
                #         result.append(elem_new)
                #     self.put_extra(result)
                _, margin_h = self.laparams.table_border_margin
                elem, extra = self.split_elem(self._cache, elem, margin_h)
                if extra:
                    self.put_extra(extra)

        self.put_cache(elem)

    def done(self):
        for elem in self._raw_cache:
            self.feed_t(elem)
            if self.cached_first():
                self.handle_extra(self._cache)
                # for el in self.handle_extra(elem):
                #      self.feed_t(el)

        if self._cache:
            self.save_cache()

        self.merge_extra()
        self.digitalize()
        if self._comments:
            self.name = self._comments[0]

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
        abs_tol, rel_tol = laparams.curver_line_tol
        mid_x = (item.x0 + item.x1) // 2
        mid_y = (item.y0 + item.y1) // 2
        margin_y = item.height * margin_h
        margin_x = item.width * margin_w
        for curve in curves:
            if curve.width * rel_tol > curve.height:
                if mid_x >= curve.x0 and mid_x <= curve.x1:
                    #if item.y1 <= curve.y1 + margin_y:
                    if mid_y < curve.y1:
                        #     ------
                        #       ab
                        # print("Top:",curve, item)
                        if not top:
                            top = curve
                        else:
                            top = get_closer(item, top, curve, 'y1')
                    #elif item.y0 >= curve.y0 - margin_y:
                    elif mid_y > curve.y0:
                        #       ab
                        #     ------
                        # print("Bottom:", curve, item)
                        if not bottom:
                            bottom = curve
                        else:
                            bottom = get_closer(item, bottom, curve, 'y0')
                    else:
                        print("Crossed curve in y direction:", curve, item, margin_y)
            elif curve.height * rel_tol > curve.width:
                if mid_y >= curve.y0 and mid_y <= curve.y1:
                    if item.x0 > curve.x0 - margin_x:
                    #if mid_x > curve.x0:
                        #   |
                        #   |   ab
                        #   |
                        # print("Left:", curve, item)
                        if not left:
                            left = curve
                        else:
                            left = get_closer(item, left, curve, 'x1')
                    #elif item.x1 < curve.x1 + margin_x:
                    elif mid_x < curve.x1:
                        #       |
                        #   ab  |
                        #       |
                        # print("Right:", curve, item)
                        if not right:
                            right = curve
                        else:
                            right = get_closer(item, right, curve, 'x0')
                    else:
                        print("Crossed curve in x direction:", curve, item, margin_x)
            else:
                print("Not curve line, discard:", curve)

        """
                            (x1, y1)
                -------------
                |    T      |
                -------------
            -----       -----      
            |   |       |   |
            |   |       |   |
            | L |       | R |
            |   |       |   |
            |   |       |   |
            -----       -----
                ---------
                |   B   |
                ---------
            (x0, y0)
            select overlapped center zone
        """
        if all((top, bottom, left, right)):
            x0 = max(top.x0 - margin_x, left.x0, bottom.x0 - margin_x)
            y0 = max(left.y0 - margin_y, bottom.y0, right.y0 - margin_y)
            x1 = min(top.x1 + margin_x, right.x1, bottom.x1 + margin_x)
            y1 = min(left.y1 + margin_y, top.y1, right.y1 + margin_y)
            #return (left.x0, bottom.y0, right.x1, top.y1)
            return (x0, y0, x1, y1)

    def probe_table(self, item, curves):
        text = item.get_text().strip()
        if self._table is None:
            result = self.pat_tab.match(text)
            if result is not None:
                self._table = TableElement(result.groups(), self.laparams)
                if result.end() != len(text):
                    self._table.put_comment(text[result.end():])
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
