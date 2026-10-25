"""Read-only adapter: bundled scanner with explicit, pruned project scope."""
import importlib.util
import json
import os
from pathlib import Path

SKILL = Path('/home/reggie/.codex/skills/code-rot-cleaner/scripts/analyze_code_rot.py')
spec = importlib.util.spec_from_file_location('code_rot_scanner', SKILL)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
scanner.EXCLUDED_DIRS.update({'runs', 'artifacts', '.workflow', '.agents', '.claude', '.codex', '.aoci', '.codegraph-cache', '.gstack', '.hyperframes'})
SOURCE_ROOTS = {'src', 'scripts', 'tests', 'provider-console'}

def scoped_walk(root, extensions):
    found = []
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in scanner.EXCLUDED_DIRS and not d.startswith('.git') and not (Path(current) / d).is_symlink())
        for name in sorted(names):
            path = Path(current) / name
            if path == root / 'index.json' or path.is_symlink() or path.suffix.lower() not in extensions:
                continue
            rel = path.relative_to(root)
            if extensions == scanner.SOURCE_EXTENSIONS and len(rel.parts) > 1 and rel.parts[0] not in SOURCE_ROOTS:
                continue
            found.append(path)
    return sorted(found)

scanner.walk_files = scoped_walk
root = Path.cwd()
data = scanner.analyze(root)
data['scope']['source_roots'] = sorted(SOURCE_ROOTS)
data['limitations'].extend([
    'Uses the bundled scanner through a scope-only adapter; the first unscoped scan was stopped without producing an analysis.',
    'Source scope: src/, scripts/, tests/, provider-console/ and root source files. References also include non-excluded documentation and configuration.',
    'Excluded: media and historical artifacts, runs, external skills, generated output, dependency/cache directories, all symlinks. No media or credential files were opened.',
    'Bundled Python resolver does not handle src-layout absolute imports or from-package imports reliably; manual AST/reference checks are required.',
    'LOC means physical lines; candidate sizes are not semantic code counts. No project-controlled command has been executed.'
])
out = root / 'outputs/code-rot-cleaner'
(out / 'analysis.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'scope': data['scope'], 'summary': data['summary']}, ensure_ascii=False, indent=2))
