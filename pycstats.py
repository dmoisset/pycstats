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


class DataStats(CodeAnalyzerBase):
    def __init__(self):
        self.indent = ""
        self.docstring_count = 0
        self.docstring_chars = 0
        self.lnotab_count = 0
        self.lnotab_bytes = 0

    def visit_ignore(self, obj): pass

    visit_NoneType = visit_int = visit_str = visit_bool = visit_float = visit_ignore

    def visit_iterable(self, it):
        for elem in it:
            self.visit(elem)

    visit_tuple = visit_frozenset = visit_iterable

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
        for const in code.co_consts:
            self.visit(const)
        self.indent = self.indent[:-4]


def main(fn):
    f = open(fn, 'rb')
    f.read(12) # Skip header
    code_obj = marshal.load(f)

    a = DataStats()
    a.visit(code_obj)

    print(f"{a.docstring_count} docstrings, {a.docstring_chars} chars")
    print(f"{a.lnotab_count} lineno tables, {a.lnotab_bytes}B")

if __name__ == "__main__":
    main(sys.argv[1])