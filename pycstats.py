#!/usr/bin/env python3

import marshal
import sys

class CodeAnalyzerBase():

    def visit(self, obj):
        # dispatch by item type
        t = type(obj).__name__
        method = getattr(self, f'visit_{t}', self.visit_default)
        method(obj)

    def visit_default(self, obj):
        print("??", type(obj))

class StandardVisitAnalyzer(CodeAnalyzerBase):

    def visit_ignore(self, obj): pass

    visit_NoneType = visit_int = visit_str = visit_bytes = visit_bool = visit_float = visit_ignore

    def visit_iterable(self, it):
        for elem in it:
            self.visit(elem)

    visit_tuple = visit_frozenset = visit_iterable

    def visit_code(self, code):
        for const in code.co_consts:
            self.visit(const)


class DataStats(StandardVisitAnalyzer):

    def __init__(self):
        self.indent = ""
        self.docstring_count = 0
        self.docstring_bytes = 0
        self.lnotab_count = 0
        self.lnotab_bytes = 0

    def visit_code(self, code):
        # print(f"{self.indent}{code.co_name}")
        self.indent += "    "

        # Docstring stats.
        if code.co_consts and not code.co_name.startswith('<') and code.co_consts[0] is not None:
            # this is an heuristic and can possibly get stuff that's not a docstring
            self.docstring_count += 1
            self.docstring_bytes += sys.getsizeof(code.co_consts[0])

        # Lnotab stats
        self.lnotab_count += 1
        self.lnotab_bytes += sys.getsizeof(code.co_lnotab)

        # Find inner code objects (inside module, class)
        super().visit_code(code)
        self.indent = self.indent[:-4]


class DupStats(StandardVisitAnalyzer):

    def __init__(self):
        self.visited = {}
        self.dup_count = 0
        self.dup_bytes = 0
        self.all_count = 0
        self.all_bytes = 0

    def visit(self, obj):
        objsize = sys.getsizeof(obj)
        if obj in self.visited:
            if id(obj) not in self.visited[obj]:
                # object is duplicate
                # print("Dup: ", repr(obj))
                self.dup_count += 1
                self.dup_bytes += objsize
                self.all_count += 1
                self.all_bytes += objsize
                self.visited[obj].add(id(obj))
            else:
                # We've seen this exact instance before. Nothing to do
                pass
        else:
            # First occurrence of the object
            self.visited[obj] = {id(obj)}
            self.all_count += 1
            self.all_bytes += objsize
        super().visit(obj)

def main(fn):
    f = open(fn, 'rb')
    f.read(12) # Skip header
    code_obj = marshal.load(f)

    a = DataStats()
    a.visit(code_obj)

    print(f"{a.docstring_count} docstrings, {a.docstring_bytes}B")
    print(f"{a.lnotab_count} lineno tables, {a.lnotab_bytes}B")

    d = DupStats()
    d.visit(code_obj)
    print(f"{d.dup_count}/{d.all_count} duplicate objects for {d.dup_bytes}/{d.all_bytes} memory size")

if __name__ == "__main__":
    main(sys.argv[1])