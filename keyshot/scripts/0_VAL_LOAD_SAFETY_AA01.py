# -*- coding: utf-8 -*-
# AUTHOR claude-opus
# REV AA01
# DEV / CI CHECK -- runs in a NORMAL Python 3 (>= 3.6), NOT inside KeyShot.
# Guards against the two things that stop a script loading in KeyShot's
# Scripting Console: (1) non-ASCII characters, (2) f-strings -- KeyShot's
# embedded interpreter is < 3.6 and its console is ASCII-sensitive, so either
# one makes the WHOLE file fail to load. This regression guard scans every
# KeyShot script in scripts/ (and scripts/archive/) and reports PASS / FAIL,
# exiting nonzero if any KeyShot-bound script would fail to load. It also flags
# walrus (:=) as a bonus > 3.5 tripwire.
#
# Why a separate dev tool and not part of 4_CHK_AUDIT: detecting f-strings needs
# ast.parse of the target file, which itself requires Python 3.6+ -- KeyShot's
# own interpreter can't even parse an f-string to check for one. So this runs on
# the dev/commit side, in the same normal Python that runs the material
# generator's py_compile checks.
#
# Run from anywhere:  python 0_VAL_LOAD_SAFETY_AA01.py [scripts_dir]
# (default scripts_dir = this file's own directory)
#
# This file is itself f-string-free + ASCII-only so it never trips its own rule,
# and it excludes itself from the scan.

import ast
import os
import sys


def non_ascii_lines(text):
    return [i + 1 for i, line in enumerate(text.splitlines())
            if any(ord(c) > 127 for c in line)]


def scan(path):
    """Return a list of human-readable problems for one file (empty = clean)."""
    problems = []
    raw = open(path, "rb").read()
    text = raw.decode("utf-8", errors="replace")

    # (1) ASCII-only (the console decodes as ASCII on the affected builds)
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        lines = non_ascii_lines(text)
        shown = ", ".join(str(n) for n in lines[:20])
        more = " (+{0} more)".format(len(lines) - 20) if len(lines) > 20 else ""
        problems.append("non-ASCII on line(s): {0}{1}".format(shown, more))

    # (2) f-strings (and walrus) via AST -- needs Python 3.6+ to parse f-strings
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        problems.append("SyntaxError while parsing (line {0}): {1}".format(
            getattr(e, "lineno", "?"), e.msg))
        return problems

    fstr = sorted({getattr(n, "lineno", 0) for n in ast.walk(tree)
                   if isinstance(n, ast.JoinedStr)})
    if fstr:
        shown = ", ".join(str(n) for n in fstr[:20])
        more = " (+{0} more)".format(len(fstr) - 20) if len(fstr) > 20 else ""
        problems.append("f-string(s) on line(s): {0}{1}".format(shown, more))

    walrus = sorted({getattr(n, "lineno", 0) for n in ast.walk(tree)
                     if n.__class__.__name__ == "NamedExpr"})
    if walrus:
        problems.append("walrus ':=' (Python 3.8+) on line(s): {0}".format(
            ", ".join(str(n) for n in walrus[:20])))
    return problems


def main():
    self_path = os.path.abspath(__file__)
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(self_path)
    root = os.path.abspath(root)

    checked = 0
    failed = 0
    print("Load-safety scan of KeyShot scripts under: {0}".format(root))
    print("-" * 68)
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            if os.path.abspath(path) == self_path:
                continue  # don't scan this dev tool itself
            checked += 1
            problems = scan(path)
            rel = os.path.relpath(path, root)
            if problems:
                failed += 1
                print("FAIL  {0}".format(rel))
                for p in problems:
                    print("        {0}".format(p))
            else:
                print("PASS  {0}".format(rel))

    print("-" * 68)
    print("{0} script(s) checked, {1} failed.".format(checked, failed))
    if failed:
        print("")
        print("FAILing scripts will NOT load in KeyShot (Python < 3.6, ASCII-only")
        print("console). Convert f-strings to \"{0}\".format(...) and replace every")
        print("non-ASCII character with ASCII. See 1_HLP_MAT_GENERATOR for the pattern.")
        sys.exit(1)
    print("All clear -- every KeyShot script is load-safe.")


if __name__ == "__main__":
    main()
