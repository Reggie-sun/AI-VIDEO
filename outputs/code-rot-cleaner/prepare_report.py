"""Build review artifacts only; never applies the proposed patch."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
root = Path.cwd()
out = root / 'outputs/code-rot-cleaner'
a = json.loads((out/'analysis.json').read_text())
(out/'scanner-analysis.json').write_text(json.dumps(a, ensure_ascii=False, indent=2)+'\n')
g = json.loads((out/'python-static.json').read_text())
manual = {
 'provider-console/src/continuity-review-contract.js': 'KEEP: continuity-review.js:2-5 multiline-imports this module and re-exports it at lines 8-14; provider-console/tests/continuity-review-contract.test.mjs also imports it. Bundled regex misses multiline imports.',
 'src/ai_video_mcp/analysis_client.py': 'KEEP: generation_feedback.py:131 launches this exact module with python -m; tests/test_generation_feedback_review.py:35 asserts the subprocess entry.',
 'src/ai_video_mcp/analysis_hook.py': 'KEEP: .codex/hooks.json:34 and .claude/settings.json:31 register this hook; tests/test_mcp_analyze.py dynamically imports it.',
 'tests/helpers/p2a_crash_worker.py': 'KEEP: tests/test_production_state_recovery.py:443 executes this helper via its string path.',
}
decisions = []
for c in a['candidates']:
    if c['id'] == 'CRT-322':
        reason = 'KEEP: continuity-review.js:79 invokes downloadHumanReviewDecision from the panel submit handler. No external export consumer does not mean the function is dead.'
    elif c['id'] == 'CRT-323':
        reason = 'KEEP: external-media-contract.js:16 and :194 invoke preferredRunBinding, including externalDisplayMetadata. The implementation is live.'
    elif c['path'] in manual:
        reason = manual[c['path']]
    elif g['inbound'].get(c['path']):
        refs = g['inbound'][c['path']]
        reason = 'KEEP: src-layout-aware AST resolves actual Python inbound import(s) from ' + ', '.join(refs[:3]) + (f' and {len(refs)-3} more' if len(refs)>3 else '') + '. See python-static.json; bundled import resolution is a false positive.'
    elif c['path'].startswith('tests/'):
        name = Path(c['path']).stem
        refs=[]
        for p in sorted((root/'tests').rglob('*.py')):
            if p != root/c['path'] and name in p.read_text(): refs.append(p.relative_to(root).as_posix())
        if not refs: raise RuntimeError('Unresolved test helper: '+c['path'])
        reason = 'KEEP: pytest uses tests/ as an import root; real helper module imports occur in ' + ', '.join(refs[:3]) + '. The generic resolver uses the repository root.'
    else:
        raise RuntimeError('Unreviewed candidate: '+c['id']+' '+c['path'])
    decisions.append({'candidate_id': c['id'], 'status': 'KEEP', 'reason': reason})

patch=[]
for ident, rel, symbol, risk, caveat in [
 ('CRT-324','src/ai_video/production/dependency.py','_source_render_pairs','low','Private function; no in-repository consumer found. Rare dynamic/external use and regression safety are unproven.'),
 ('CRT-325','src/ai_video/production/manifest_schema.py','is_supported_manifest_version','medium','Public module function; external imports cannot be ruled out, and passing in-repository tests would not prove external API compatibility.'),
]:
    p=root/rel
    text=p.read_text()
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==symbol)
    lines=text.splitlines(keepends=True)
    block=''.join(lines[node.lineno-1:node.end_lineno])
    changed=''.join(lines[:node.lineno-1]+lines[node.end_lineno:])
    ast.parse(changed)
    patch.extend(difflib.unified_diff(lines, changed.splitlines(keepends=True), fromfile='a/'+rel, tofile='b/'+rel))
    a['candidates'].append({'id':ident,'category':'unused-export','subject':symbol+' from '+rel,'path':rel,'line':node.lineno,'end_line':node.end_lineno,'confidence':'high' if risk=='low' else 'medium','initial_status':'REVIEW','risk':risk,'proof_eligible':False,'loc':node.end_lineno-node.lineno+1,'bytes':len(block.encode()),'evidence':['Supplementary AST module-symbol check, including import aliases, found no inbound symbol reference.','Bounded repository search found only the definition; generated CodeGraph index, artifacts, runs, output reports and third-party skills were excluded.']+(['CodeGraph relationship query returned an empty list; advisory only.'] if ident=='CRT-324' else []),'caveats':[caveat,'The bundled proof script deletes whole files, so it must not be used to delete this live module. Proof must target only the proposed function block in fresh disposable copies. No approved commands have been run.']})
    decisions.append({'candidate_id':ident,'status':'REVIEW','reason':caveat+' Proposed function-only patch is syntax-valid but has no execution proof.'})
a['summary']['candidates']=len(a['candidates'])
a['summary']['by_category']['unused-export']+=2
a['summary']['supplementary_review_loc']=sum(c['loc'] for c in a['candidates'] if c['id'] in {'CRT-324','CRT-325'})
a['limitations'].extend(['Root index.json is a derived CodeGraph index and was excluded from text evidence.','Raw scanner file-size estimate is NOT an approved or proven deletion amount. All original 323 candidates were rejected after import/internal-use/entry-point verification.','CRT-324 and CRT-325 are supplemental function-block candidates, not whole-file deletions. They stay REVIEW without focused execution proof.'])
(out/'analysis.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(out/'review.json').write_text(json.dumps({'decisions':decisions},ensure_ascii=False,indent=2)+'\n')
(out/'proposed-cleanup.patch').write_text(''.join(patch))
print(json.dumps({'review':[{k:c[k] for k in ('id','path','subject','loc','bytes','risk')} for c in a['candidates'][-2:]],'keep':len(decisions)-2},ensure_ascii=False,indent=2))
