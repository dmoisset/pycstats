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

    visit_int = visit_str = visit_bytes = visit_bool = visit_float = visit_complex = visit_ignore
    visit_NoneType = visit_ellipsis = visit_ignore

    def visit_iterable(self, it):
        for elem in it:
            self.visit(elem)

    visit_tuple = visit_frozenset = visit_iterable

    def visit_code(self, code):
        self.visit(code.co_argcount)
        self.visit(code.co_kwonlyargcount)
        self.visit(code.co_nlocals)
        self.visit(code.co_stacksize)
        self.visit(code.co_flags)
        self.visit(code.co_code)
        self.visit(code.co_consts)
        self.visit(code.co_names)
        self.visit(code.co_varnames)
        self.visit(code.co_freevars)
        self.visit(code.co_cellvars)
        self.visit(code.co_filename)
        self.visit(code.co_name)
        self.visit(code.co_firstlineno)
        self.visit(code.co_lnotab)

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

    def reset_objects(self):
        self.visited = {}

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


def main(*fns):
    a = DataStats()
    d = DupStats()

    for fn in fns:
        f = open(fn, 'rb')
        f.read(12) # Skip header
        code_obj = marshal.load(f)

        a.visit(code_obj)
        d.visit(code_obj)

        # Uncommenting the next line will measure repeats only within a module, which is
        # more correct considering that values probably can be shared only within a module, but
        # will also count cpython singletons like True/False/None/42 once per module where they
        # appear
        # d.reset_objects()

    print(f"{a.docstring_count} docstrings, {a.docstring_bytes}B")
    print(f"{a.lnotab_count} lineno tables, {a.lnotab_bytes}B")
    print(f"{d.dup_count}/{d.all_count} duplicate objects for {d.dup_bytes}/{d.all_bytes} memory size")

if __name__ == "__main__":
    main(*sys.argv[1:])