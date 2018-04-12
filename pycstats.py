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

    visit_NoneType = visit_int = visit_str = visit_bool = visit_float = visit_ignore

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
        self.docstring_chars = 0
        self.lnotab_count = 0
        self.lnotab_bytes = 0

    def visit_code(self, code):
        # print(f"{self.indent}{code.co_name}")
        self.indent += "    "

        # Docstring stats.
        if code.co_consts and not code.co_name.startswith('<') and code.co_consts[0] is not None:
            self.docstring_count += 1
            self.docstring_chars += len(code.co_consts[0]) # FIXME: How can I get the amount of string storage used?

        # Lnotab stats
        self.lnotab_count += 1
        self.lnotab_bytes += len(code.co_lnotab)

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
        self.all_count += 1
        self.all_bytes += sys.getsizeof(obj)
        if obj in self.visited and id(obj) not in self.visited[obj]:
            # object is duplicate
            print("Dup:", obj)
            self.dup_count += 1
            self.dup_bytes += sys.getsizeof(obj)
        self.visited.setdefault(obj, set()).add(id(obj))
        super().visit(obj)

def main(fn):
    f = open(fn, 'rb')
    f.read(12) # Skip header
    code_obj = marshal.load(f)

    a = DataStats()
    a.visit(code_obj)

    print(f"{a.docstring_count} docstrings, {a.docstring_chars} chars")
    print(f"{a.lnotab_count} lineno tables, {a.lnotab_bytes}B")

    d = DupStats()
    d.visit(code_obj)
    print(f"{d.dup_count}/{d.all_count} duplicate objects for {d.dup_bytes}/{d.all_bytes} memory size")

if __name__ == "__main__":
    main(sys.argv[1])