"""Static src-layout import graph; parses bytes, never imports project modules."""
import ast
import collections
import hashlib
import json
import subprocess
from pathlib import Path
root = Path.cwd()
paths = sorted(p for base in ('src', 'scripts', 'tests') for p in (root / base).rglob('*.py') if '__pycache__' not in p.parts and not p.is_symlink())
modules = {}
for p in paths:
    parts = list(p.relative_to(root).with_suffix('').parts)
    if parts[0] == 'src':
        parts = parts[1:]
    if parts[-1] == '__init__':
        parts.pop()
    modules['.'.join(parts)] = p.relative_to(root).as_posix()
inbound = collections.defaultdict(set)
identifiers = collections.Counter()
parsed = {}
errors = []
for p in paths:
    rel = p.relative_to(root).as_posix()
    try:
        tree = ast.parse(p.read_text(), filename=rel)
    except (SyntaxError, UnicodeError) as e:
        errors.append({'path': rel, 'error': str(e)})
        continue
    parsed[rel] = tree
    for n in ast.walk(tree):
        if isinstance(n, ast.Name): identifiers[n.id] += 1
        elif isinstance(n, ast.Attribute): identifiers[n.attr] += 1
        elif isinstance(n, ast.keyword) and n.arg: identifiers[n.arg] += 1
        elif isinstance(n, ast.alias): identifiers[n.name.split('.')[-1]] += 1
        if isinstance(n, ast.Import):
            specs = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            current = next(k for k, v in modules.items() if v == rel)
            package = current if p.name == '__init__.py' else current.rpartition('.')[0]
            if n.level:
                parts = package.split('.') if package else []
                base = '.'.join(parts[:len(parts) - n.level + 1])
                if n.module: base = '.'.join(filter(None, (base, n.module)))
            else: base = n.module or ''
            specs = [base] + ['.'.join(filter(None, (base, a.name))) for a in n.names]
        else: continue
        for module in specs:
            if module in modules and modules[module] != rel: inbound[modules[module]].add(rel)
orphans = []
symbols = []
for rel, tree in parsed.items():
    path = root / rel
    if rel.startswith('src/') and path.name not in ('__init__.py','__main__.py') and not inbound[rel]:
        orphans.append({'path': rel, 'loc': len(path.read_text().splitlines()), 'definitions': [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]})
    if rel.startswith('src/'):
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and identifiers[n.name] == 0:
                symbols.append({'path': rel, 'name': n.name, 'line': n.lineno, 'end_line': n.end_lineno, 'loc': n.end_lineno - n.lineno + 1, 'decorated': bool(n.decorator_list)})
out = {'mode': 'static-only', 'parse_errors': errors, 'python_files': len(paths), 'src_layout_orphans': orphans, 'unreferenced_module_functions': symbols, 'inbound': {k: sorted(v) for k, v in sorted(inbound.items())}, 'source_hashes': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}, 'head': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()}
(root/'outputs/code-rot-cleaner/python-static.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'python_files': len(paths), 'parse_errors': errors, 'src_layout_orphans': orphans, 'unreferenced_module_functions': symbols}, ensure_ascii=False, indent=2))
