# -*- coding: utf-8 -*-
# AUTHOR claude-opus
# REV AA09
# DEV / CI CHECK -- runs in a NORMAL Python 3 (>= 3.6), NOT inside KeyShot.
# Scans every KeyShot script in scripts/ (and scripts/archive/) and reports
# PASS / FAIL, exiting nonzero on any failure. Checks, and the failure mode
# each guards against:
#   - non-ASCII chars, f-strings, walrus (:=) -- KeyShot's embedded
#     interpreter is < 3.6 and its console is ASCII-sensitive; any of these
#     makes the whole file fail to load.
#   - inline <script> blocks in the sibling keyshot/*.html pages, parsed with
#     "node --check" -- these pages have no build step, so one bad character
#     inside an inline script silently blanks the whole page. SKIPPED with a
#     note (never a false PASS) if node is absent.
#   - IMPORT of each script against a stub lux module -- proves module level
#     actually executes, catching a name used before it is defined (which
#     py_compile and an AST pass over function bodies both miss). Scripts
#     that call main() at module level are SKIPPED, since importing them
#     would run them.
#   - every lux.<name> call checked against keyshot/lux_api_surface.json
#     (harvested from a real dir(lux) dump) -- a stub import proves a script
#     LOADS, not that the API it calls exists. Unknown name = FAIL; verify on
#     the build and add it to the surface file rather than removing the check.
#   - CORE BLOCK byte-identity across generator scripts -- the shared plumbing
#     is duplicated verbatim per file (no shared module, since the KeyShot
#     machine has no git and downloads one file per run); copies that differ
#     are a FAIL so drift is caught as a build failure.
#   - DRY RUN: drives DEFAULT_OPTIONS -> sample_spec -> validate_spec ->
#     build -> emit_spec against the stub -- catches bugs that only surface
#     once a material is actually built, which import alone does not execute.
#     Scripts without that shape are skipped with a note.
#   - REV consistency: content changed under an unchanged filename is a FAIL
#     against git HEAD (the KeyShot machine has no git and downloads by name,
#     so same-name-different-contents is invisible there); and the three REV
#     markers -- filename suffix, "# REV" header, any *_REV banner constant --
#     must agree, since a pasted console log is only traceable via the name.
#
# Runs dev-side (not part of 4_CHK_AUDIT) because f-string detection needs
# ast.parse, which itself requires Python 3.6+ -- KeyShot's own interpreter
# can't parse an f-string to check for one.
#
# Run from anywhere:  python 0_VAL_LOAD_SAFETY_AA09.py [scripts_dir]
# (default scripts_dir = this file's own directory)
#
# This file is itself f-string-free + ASCII-only so it never trips its own
# rule, and it excludes itself from the scan.

import ast
import io
import json
import os
import re
import subprocess
import sys
import tempfile


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


INLINE_SCRIPT_RE = re.compile(r"<script(?![^>]*src=)[^>]*>(.*?)</script>",
                              re.S | re.I)


def node_available():
    try:
        subprocess.check_output(["node", "--version"],
                                stderr=subprocess.STDOUT)
        return True
    except Exception:
        return False


def scan_html(path):
    """Parse every inline <script> block in an HTML page with node --check.
    Returns a list of problem strings (empty = clean)."""
    problems = []
    try:
        source = io.open(path, encoding="utf-8").read()
    except Exception as e:
        return ["couldn't read: {0}".format(e)]
    blocks = INLINE_SCRIPT_RE.findall(source)
    if not blocks:
        return problems
    joined = "\n;\n".join(blocks)
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False,
                                      encoding="utf-8")
    try:
        tmp.write(joined)
        tmp.close()
        proc = subprocess.Popen(["node", "--check", tmp.name],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.communicate()[0]
        if proc.returncode != 0:
            detail = out.decode("utf-8", "replace").strip().replace("\n", " | ")
            problems.append("inline JS does not parse -- the page will render "
                            "EMPTY: {0}".format(detail[:400]))
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
    return problems


def scan_html_pages(scripts_root):
    """Check the HTML pages that live beside scripts/ (keyshot/*.html).
    Returns (checked, failed)."""
    page_dir = os.path.dirname(scripts_root)
    if os.path.basename(scripts_root).lower() != "scripts":
        page_dir = scripts_root
    pages = [os.path.join(page_dir, fn) for fn in sorted(os.listdir(page_dir))
             if fn.lower().endswith(".html")] if os.path.isdir(page_dir) else []
    if not pages:
        return 0, 0
    print("")
    print("HTML pages (inline JS) in: {0}".format(page_dir))
    print("-" * 68)
    if not node_available():
        print("SKIP  node not found -- inline JS NOT checked. Install node, or")
        print("      review any HTML edit by hand: a broken string blanks the page.")
        return 0, 0
    checked = 0
    failed = 0
    for path in pages:
        checked += 1
        problems = scan_html(path)
        name = os.path.basename(path)
        if problems:
            failed += 1
            print("FAIL  {0}".format(name))
            for p in problems:
                print("        {0}".format(p))
        else:
            print("PASS  {0}".format(name))
    return checked, failed


CORE_START = "# ===== CORE BLOCK"
CORE_END = "# ===== END CORE BLOCK"


def extract_core_block(path):
    """Return the CORE BLOCK text of a script, or None if it has none."""
    try:
        source = io.open(path, encoding="utf-8").read()
    except Exception:
        return None
    i = source.find(CORE_START)
    if i < 0:
        return None
    j = source.find(CORE_END, i)
    if j < 0:
        return None
    return source[i:j]


def check_core_shadowing(paths):
    """A script must not REDEFINE a name the CORE BLOCK defines.

    Guards a failure mode byte-identity cannot see: a local function defined
    AFTER the CORE BLOCK with the same name as one inside it. Python takes
    the later definition, so the block stays byte-identical across files
    while the shared function is unreachable and silently dead in that one --
    invisible to the identity check (text matches), the import check (loads
    fine), and a render (nothing calls the dead path yet). Byte-identity
    proves the TEXT is shared; this proves the text still MEANS what it says
    in each file.
    """
    print("")
    print("CORE BLOCK shadowing -- no script may redefine a shared name")
    print("-" * 68)
    checked = failed = 0
    for path in paths:
        block = extract_core_block(path)
        if block is None:
            continue
        try:
            source = io.open(path, encoding="utf-8").read()
        except Exception:
            continue
        after = source.split(CORE_END, 1)
        if len(after) < 2:
            continue
        before = source[:source.find(CORE_START)]
        outside = before + after[1]
        shared = set()
        for line in block.splitlines():
            if line.startswith("def "):
                shared.add(line[4:].split("(")[0].strip())
        clashes = []
        for line in outside.splitlines():
            if not line.startswith("def "):
                continue
            name = line[4:].split("(")[0].strip()
            if name in shared:
                clashes.append(name)
        checked += 1
        name = os.path.basename(path)
        if clashes:
            failed += 1
            print("FAIL  {0}".format(name))
            for clash in sorted(set(clashes)):
                print("        redefines '{0}', which the CORE BLOCK also "
                      "defines".format(clash))
            print("        The later definition WINS, so the shared one is dead "
                  "code here.")
            print("        Rename the local one. Do not edit the block.")
        else:
            print("PASS  {0} -- no shared name redefined".format(name))
    return checked, failed


def check_core_blocks(paths):
    """Every CORE BLOCK must be byte-identical. Reports the first differing line,
    which is enough to show whether someone edited one copy in place."""
    blocks = []
    for path in paths:
        block = extract_core_block(path)
        if block is not None:
            blocks.append((os.path.basename(path), block))
    if len(blocks) < 2:
        return 0, 0, len(blocks)
    print("")
    print("CORE BLOCK -- must be byte-identical across generators")
    print("-" * 68)
    ref_name, ref = blocks[0]
    failed = 0
    for name, block in blocks[1:]:
        if block == ref:
            print("PASS  {0} matches {1}".format(name, ref_name))
            continue
        failed += 1
        a = ref.splitlines()
        b = block.splitlines()
        where = "length differs ({0} vs {1} lines)".format(len(a), len(b))
        for n in range(min(len(a), len(b))):
            if a[n] != b[n]:
                where = "first difference at block line {0}: {1} has {2!r}, {3} has {4!r}".format(
                    n + 1, ref_name, a[n].strip()[:60], name, b[n].strip()[:60])
                break
        print("FAIL  {0} has DRIFTED from {1}".format(name, ref_name))
        print("        {0}".format(where))
        print("        Fix by copying the whole block across. Do not hand-merge.")
    return len(blocks), failed, len(blocks)


def load_lux_surface(scripts_root):
    """Names observed on the real lux module. Returns (set, path) or (None, path)
    if the harvest file is absent, in which case the check is skipped loudly."""
    page_dir = os.path.dirname(scripts_root)
    if os.path.basename(scripts_root).lower() != "scripts":
        page_dir = scripts_root
    path = os.path.join(page_dir, "lux_api_surface.json")
    if not os.path.isfile(path):
        return None, path
    try:
        data = json.loads(io.open(path, encoding="utf-8").read())
        return set(data.get("names", [])), path
    except Exception:
        return None, path


def scan_lux_names(path, surface):
    """Flag any lux.<name> the real module does not have. This is the check the
    stub import cannot do: a stub answers to every attribute, so an import proves
    a script LOADS and nothing about whether the API it calls exists.

    Uses the AST, not a regex, so prose (a doc URL, a docstring listing
    candidate names) is not mistaken for a call. Names reached through
    getattr(lux, "name", None) are deliberately NOT flagged: that IS the
    guarded pattern, and absence is handled there."""
    if surface is None:
        return []
    try:
        tree = ast.parse(io.open(path, encoding="utf-8").read())
    except SyntaxError:
        return []  # the AST/ASCII scan above already reported it
    unknown = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        base = node.value
        if isinstance(base, ast.Name) and base.id == "lux":
            if node.attr not in surface:
                unknown.add(node.attr)
    if not unknown:
        return []
    return ["calls lux.{0} -- not on the observed build (13.2.0.184). Verify on "
            "the machine and add it to lux_api_surface.json, or use the name that "
            "exists, or reach it through getattr(lux, name, None) if you are "
            "deliberately probing. Do NOT delete this check.".format(
                ", lux.".join(sorted(unknown)))]


STUB_IMPORT = """
import sys, types, io
class Any(object):
    def __init__(self, name="lux"): self._n = name
    def __getattr__(self, k): return Any(self._n + "." + k)
    def __call__(self, *a, **k): return Any(self._n + "()")
    def __iter__(self): return iter([])
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __bool__(self): return False
    def __nonzero__(self): return False
for mod in ("lux", "luxmath"):
    m = types.ModuleType(mod)
    m.__getattr__ = lambda k, _m=mod: Any(_m + "." + k)
    sys.modules[mod] = m
path = sys.argv[1]
src = io.open(path, encoding="utf-8").read()
ns = {"__name__": "not_main", "__file__": path}
exec(compile(src, path, "exec"), ns)
print("IMPORT OK")
"""


def self_executing(path):
    '''True if the file calls main() at module level rather than guarding it.
    Importing one of those would RUN it, so it is skipped rather than executed.'''
    try:
        source = io.open(path, encoding="utf-8").read()
    except Exception:
        return True
    for line in source.splitlines():
        if line.strip() == "main()" and not line.startswith((" ", "	")):
            return True
    return False


def scan_import(path, runner):
    """Execute the script's module level against a stub lux. This is the only
    check that catches a name used before it is defined, which is what "will it
    load" actually means. Returns a list of problems."""
    try:
        proc = subprocess.Popen([sys.executable, runner, path],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.communicate()[0].decode("utf-8", "replace")
    except Exception as e:
        return ["couldn't run the import check: {0}".format(e)]
    if proc.returncode == 0 and "IMPORT OK" in out:
        return []
    tail = [ln for ln in out.strip().splitlines() if ln.strip()][-3:]
    return ["module level FAILED to execute (this is what a KeyShot load does): "
            + " | ".join(tail)]


DRY_RUN = STUB_IMPORT.replace('print("IMPORT OK")', """
if "DEFAULT_OPTIONS" not in ns or "sample_spec" not in ns:
    print("DRY RUN SKIPPED")
else:
    _spec = ns["sample_spec"](dict(ns["DEFAULT_OPTIONS"]))
    if "validate_spec" in ns:
        _spec = ns["validate_spec"](_spec)
    for _b in ("build_material", "build_paint"):
        if _b in ns:
            ns[_b](_spec)
    if "emit_spec" in ns:
        ns["emit_spec"](_spec)
    print("DRY RUN OK")
""")


def scan_dryrun(path, runner):
    """Drive the real build pipeline against the stub lux. Catches the whole class
    of bug that only appears once a material is actually built: a helper called
    with the wrong argument, a key that does not exist, a None where a node was
    expected. Nothing else here executes that code at all."""
    try:
        proc = subprocess.Popen([sys.executable, runner, path],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.communicate()[0].decode("utf-8", "replace")
    except Exception as e:
        return ["couldn't run the dry run: {0}".format(e)]
    if proc.returncode == 0 and ("DRY RUN OK" in out or "DRY RUN SKIPPED" in out):
        return []
    tail = [ln for ln in out.strip().splitlines() if ln.strip()][-3:]
    return ["DRY RUN failed -- building a material raises: " + " | ".join(tail)]


def write_runner(source):
    """Write a stub runner to a temp file; returns its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False,
                                      encoding="utf-8")
    tmp.write(source)
    tmp.close()
    return tmp.name


def write_stub_runner():
    """Write the stub-lux runner to a temp file; returns its path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False,
                                      encoding="utf-8")
    tmp.write(STUB_IMPORT)
    tmp.close()
    return tmp.name


REV_IN_NAME = re.compile(r"_([A-Z]{2}\d{2})\.py$")
REV_IN_HEADER = re.compile(r"^#\s*REV\s+([A-Z]{2}\d{2})\s*$", re.M)
REV_IN_BANNER = re.compile(r"^[A-Z_]*REV\s*=\s*[\"']([A-Z]{2}\d{2})[\"']", re.M)


def check_rev_agreement(paths, root):
    """The filename suffix, the '# REV' header and the banner constant must all
    name the same rev. A script whose log says AA07 and whose filename says AA06
    cannot be traced back from a pasted console dump, which is what the log is
    for. Files with no rev in the name are skipped (not every script carries one)."""
    checked = 0
    failed = 0
    print("")
    print("REV agreement -- filename, '# REV' header, console banner")
    print("-" * 68)
    for path in paths:
        name = os.path.basename(path)
        in_name = REV_IN_NAME.search(name)
        if not in_name:
            continue
        checked += 1
        rev = in_name.group(1)
        try:
            with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except Exception as e:
            print("FAIL  {0}: could not read ({1})".format(name, e))
            failed += 1
            continue
        problems = []
        header = REV_IN_HEADER.search(text)
        if header is None:
            problems.append("no '# REV <rev>' header line")
        elif header.group(1) != rev:
            problems.append("header says {0}, filename says {1}".format(
                header.group(1), rev))
        for banner in REV_IN_BANNER.finditer(text):
            if banner.group(1) != rev:
                problems.append("banner constant says {0}, filename says {1}".format(
                    banner.group(1), rev))
        if problems:
            failed += 1
            print("FAIL  {0}".format(os.path.relpath(path, root)))
            for p in problems:
                print("        {0}".format(p))
        else:
            print("PASS  {0} -- all three say {1}".format(
                os.path.relpath(path, root), rev))
    return checked, failed


def check_rev_bumped(root):
    """Content changed under an unchanged filename = the KeyShot machine cannot
    tell the new version from the old one, because it downloads by name and has
    no git. Renames are invisible to --diff-filter=M, so the correct workflow
    (git mv + edit) passes cleanly."""
    print("")
    print("REV bump -- content must not change under an unchanged filename")
    print("-" * 68)
    try:
        proc = subprocess.Popen(
            ["git", "diff", "--name-only", "--diff-filter=M", "HEAD", "--", root],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=root)
        out, err = proc.communicate()
    except Exception as e:
        print("[note] git unavailable ({0}) -- in-place-edit check SKIPPED. "
              "A script edited without a REV bump will NOT be caught.".format(e))
        return 0, 0
    if proc.returncode != 0:
        detail = err.decode("utf-8", "replace").strip().splitlines()
        detail = detail[0] if detail else "unknown error"
        print("[note] not a git work tree ({0}) -- in-place-edit check "
              "SKIPPED.".format(detail))
        return 0, 0
    changed = []
    for line in out.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if line.endswith(".py") and "/scripts/" in line.replace("\\", "/"):
            changed.append(line)
    if not changed:
        print("PASS  no script has been edited in place since HEAD")
        return 1, 0
    print("FAIL  {0} script(s) edited in place, filename unchanged:".format(
        len(changed)))
    for line in changed:
        print("        {0}".format(line))
    print("")
    print("        The KeyShot machine downloads ONE file BY NAME and has no git,")
    print("        so same-name-different-contents is invisible over there. It ran")
    print("        a stale probe for an hour on 2026-08-03 for exactly this reason.")
    print("        Fix: git mv to the next REV, bump the '# REV' header and the")
    print("        banner constant, and move the site refs (scripts.html SCRIPTS +")
    print("        UPDATED map) in the SAME commit; update the lab docs too.")
    return 1, 1


def main():
    self_path = os.path.abspath(__file__)
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(self_path)
    root = os.path.abspath(root)

    checked = 0
    failed = 0
    runner = write_stub_runner()
    dry_runner = write_runner(DRY_RUN)
    lux_surface, surface_path = load_lux_surface(root)
    if lux_surface is None:
        print("[note] {0} not found -- lux NAME check skipped (a guessed API name "
              "will not be caught)".format(os.path.basename(surface_path)))
    else:
        print("[note] lux name check against {0} observed names".format(len(lux_surface)))
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
            if not problems:
                if self_executing(path):
                    problems_note = " (import check skipped: runs itself)"
                else:
                    problems += scan_import(path, runner)
                    problems += scan_dryrun(path, dry_runner)
                    problems_note = ""
                problems += scan_lux_names(path, lux_surface)
            else:
                problems_note = ""
            rel = os.path.relpath(path, root) + problems_note
            if problems:
                failed += 1
                print("FAIL  {0}".format(rel))
                for p in problems:
                    print("        {0}".format(p))
            else:
                print("PASS  {0}".format(rel))

    for tmp_path in (runner, dry_runner):
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    core_paths = []
    for dirpath, _dn, fns in os.walk(root):
        for fn in sorted(fns):
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            if os.path.abspath(full) == self_path:
                continue  # this file NAMES the markers; it does not carry a block
            core_paths.append(full)
    core_checked, core_failed, core_seen = check_core_blocks(core_paths)
    checked += core_checked
    failed += core_failed
    if core_seen == 1:
        print("")
        print("[note] only one file carries a CORE BLOCK -- nothing to compare")

    shadow_checked, shadow_failed = check_core_shadowing(core_paths)
    checked += shadow_checked
    failed += shadow_failed

    rev_checked, rev_failed = check_rev_agreement(core_paths, root)
    checked += rev_checked
    failed += rev_failed

    bump_checked, bump_failed = check_rev_bumped(root)
    checked += bump_checked
    failed += bump_failed

    html_checked, html_failed = scan_html_pages(root)
    checked += html_checked
    failed += html_failed

    print("-" * 68)
    print("{0} file(s) checked, {1} failed.".format(checked, failed))
    if failed:
        print("")
        print("FAILing scripts will NOT load in KeyShot (Python < 3.6, ASCII-only")
        print("console). Convert f-strings to \"{0}\".format(...) and replace every")
        print("non-ASCII character with ASCII. See 1_HLP_MAT_GENERATOR for the pattern.")
        sys.exit(1)
    print("All clear -- every KeyShot script is load-safe and every page's "
          "inline JS parses.")


if __name__ == "__main__":
    main()
