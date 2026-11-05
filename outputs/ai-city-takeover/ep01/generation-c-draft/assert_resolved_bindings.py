"""Verify actual resolved C bindings after canonical prepare, never infer send order."""
from pathlib import Path
import argparse
import json
P=Path(__file__).resolve().parent

def validate(prepared):
    request=prepared.get('resolved_request',prepared)
    if not request:raise ValueError('No resolved request; native reference order is not evaluated')
    refs=request['image_bindings']
    selected=json.loads((P/'source-selections.json').read_text())
    # This is the order authored in the draft's explicit native numbered duties.
    # It becomes a verified actual order ONLY after comparison against this exact request.
    expected=['iris-c-interior','iris-cf-details']
    if [x['asset_id'] for x in refs] != expected:raise ValueError('Actual resolved order differs; revise authored numbered duties before submit')
    by_id={x['asset_id']:x for x in selected}
    for binding in refs:
        source=by_id[binding['asset_id']]
        if binding['asset_sha256']!=source['sha256'] or binding['size_bytes']!=source['size_bytes'] or binding['role']!='reference':
            raise ValueError('Resolved reference identity/role differs from approved C source')
    text=request['prompt_text']
    if not all(fragment in text for fragment in ('第一张已认可室内图','第二张已认可正面头胸身份图控制同一女性的完整面貌、身份、左耳装置和左领极细红线','观察者看到的始终是显示器背面','不向背面贴图')):
        raise ValueError('Resolved prompt omits authored C reference duties / monitor-back constraint')
    if '阳台' in text:raise ValueError('C prompt inherited a balcony direction')
    return {'actual_reference_order_verified':True,'resolved_generation_hash':request['resolved_generation_hash'],'actual_quality':'NOT_EVALUATED'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('prepared',type=Path);args=parser.parse_args()
    print(json.dumps(validate(json.loads(args.prepared.read_text())),ensure_ascii=False))
if __name__=='__main__':main()
