#!/usr/bin/env python3
"""Makes vabaxos_screen_reader/orca48_map.py (block 9, ADR-0027): the Orca 48
settings for the (group, key) names of the settings pages, which are Orca
50's. Orca 50 declares, for every setting, its older JSON name
(migration_key of its @gsetting decorators); this reads them with ast,
without running Orca 50, and takes the defaults from Orca 48's settings.

    make-orca48-map.py ORCA50_PYTHON_DIR ORCA48_PYTHON_DIR > orca48_map.py

Each argument is a dist-packages folder with an orca/ package in it (for
example from the unpacked .deb of Orca 50.2 and of Orca 48.1).
"""
import ast, glob, json, os, re, subprocess, sys

ORCA50, ORCA48 = sys.argv[1], sys.argv[2]
src = os.path.join(ORCA50, "orca")
consts = {}      # module-level and class-level NAME = "string"
modconsts = {}
def const_value(node, scope):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return scope.get(node.id, modconsts.get(node.id))
    if isinstance(node, ast.Attribute):
        return scope.get(node.attr, modconsts.get(node.attr))
    return None

settings, enums = [], {}
for path in sorted(glob.glob(os.path.join(src, "*.py"))):
    tree = ast.parse(open(path).read())
    mod = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            for t in n.targets:
                if isinstance(t, ast.Name): mod[t.id] = n.value.value
    modconsts.update(mod)
    def walk(node, scope):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                cs = dict(scope)
                for n in child.body:
                    if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                        for t in n.targets:
                            if isinstance(t, ast.Name): cs[t.id] = n.value.value
                for dec in child.decorator_list:
                    if isinstance(dec, ast.Call) and getattr(dec.func, "attr", "") == "gsettings_enum":
                        eid = const_value(dec.args[0], cs) if dec.args else const_value(next(k.value for k in dec.keywords if k.arg == "enum_id"), cs)
                        vals = next((k.value for k in dec.keywords if k.arg == "values"), dec.args[1] if len(dec.args) > 1 else None)
                        try:
                            enums[eid] = ast.literal_eval(vals)
                        except Exception:
                            enums[eid] = None
                walk(child, cs)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in child.decorator_list:
                    if isinstance(dec, ast.Call) and getattr(dec.func, "attr", "") == "gsetting":
                        kw = {k.arg: k.value for k in dec.keywords}
                        item = {a: const_value(kw[a], scope) for a in ("key", "schema", "gtype", "genum", "voice_type", "migration_key") if a in kw}
                        try:
                            item["default"] = ast.literal_eval(kw["default"])
                        except Exception:
                            item["default"] = None
                        item["module"] = os.path.basename(path)
                        settings.append(item)
                walk(child, scope)
            else:
                walk(child, scope)
    walk(tree, mod)

d = {"settings": settings, "enums": enums}
sys.path.insert(0, ORCA48)
import orca.settings as s48  # noqa: E402
enums = d['enums']
src = subprocess.run(['grep', '-rhoE', r"get_setting\(['\"][A-Za-z]+['\"]\)", os.path.join(ORCA48, 'orca')], capture_output=True, text=True).stdout
read48 = set(re.findall(r"get_setting\(['\"]([A-Za-z]+)['\"]\)", src))
ALIASES = {"progressBarSpeechVerbosity": "progressBarVerbosity", "progressBarSpeechInterval": "progressBarUpdateInterval"}
# Script settings with their script defaults (web script sets them when unset).
SCRIPT_DEFAULTS = {"sayAllOnLoad": True, "pageSummaryOnLoad": True, "caretNavigationEnabled": True,
                   "structuralNavigationEnabled": True}
rows = {}
skipped = []
for x in d['settings']:
    m = x.get('migration_key')
    if not m or x['schema'] in ('voice', 'keybindings', 'metadata', 'pronunciations'):
        continue
    m = ALIASES.get(m, m)
    if not (m in s48.userCustomizableSettings or m in read48 or hasattr(s48, m)):
        skipped.append((x['schema'], x['key'], m)); continue
    default = getattr(s48, m, SCRIPT_DEFAULTS.get(m))
    if x.get('genum'):
        values = enums.get(x['genum']) or {}
        kind = 'strenum' if isinstance(default, str) else 'enum'
        rows[(x['schema'], x['key'])] = (m, kind, default, values)
    else:
        kind = {'b': 'bool', 'i': 'int', 'd': 'float', 's': 'str', 'as': 'strv'}.get(x.get('gtype'), 'str')
        rows[(x['schema'], x['key'])] = (m, kind, default, None)
print(len(rows), 'mapped;', len(skipped), 'not in Orca 48', file=sys.stderr)
SPDX = "SPDX"  # split, so REUSE does not read the header below as this file's
out = ['# %s-FileCopyrightText: 2026 Vabax and VabaxOS contributors' % SPDX,
       '# %s-License-Identifier: GPL-3.0-or-later' % SPDX,
       '"""Orca 48\'s settings for the names of the settings pages (block 9, ADR-0027).',
       '',
       'The pages name each setting as Orca 50 did in dconf, (group, key). Orca 48',
       '(Debian 13) keeps them in JSON under its older names. Made from the',
       'mapping that Orca 50.2 declares for its migration from JSON (migration_key',
       'of every setting) and from the defaults of Orca 48.1 (orca/settings.py):',
       '(group, key): (Orca 48 name, kind, Orca 48 default, {nick: number} or None).',
       'kind: bool, int, float, str, strv, enum (the JSON value is the number of',
       'the nick) or strenum (the JSON value is the nick itself).',
       '',
       'Settings of Orca 50 that Orca 48 does not have are missing here: the pages',
       'hide them.',
       '"""',
       '',
       'SETTINGS = {']
for k in sorted(rows):
    out.append('    %r: %r,' % (k, rows[k]))
out += ['}', '', '# Orca 50 settings without an Orca 48 counterpart, for the record.', 'MISSING = [']
for k in sorted(skipped):
    out.append('    %r,' % (k,))
out += [']', '']
sys.stdout.write('\n'.join(out))
