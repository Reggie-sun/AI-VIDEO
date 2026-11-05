"""Read-only offline prepare. No transport or authorizer supplied."""
from pathlib import Path
import json,dataclasses,enum
from scripts.jimeng_feedback_driver import load_configuration,create_runtime
HERE=Path(__file__).resolve().parent
ROOT=Path.cwd()/'runs/shizhen-awesome-remake-20261104/municipal'
def plain(x):
 if hasattr(x,'model_dump'): return x.model_dump(mode='json')
 if dataclasses.is_dataclass(x): return {f.name:plain(getattr(x,f.name)) for f in dataclasses.fields(x) if f.name not in ('provider',)}
 if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [plain(v) for v in x]
 if isinstance(x,(Path,enum.Enum)):return str(x.value if isinstance(x,enum.Enum) else x)
 if x is None or isinstance(x,(str,int,float,bool)):return x
 return type(x).__name__
runtime=create_runtime(project_root=ROOT,configuration=load_configuration(HERE/'driver-configuration.json'))
p=runtime.prepare()
result={'live_transport_supplied':runtime.live_transport_supplied,'video_calls':0,'prepared':plain(p)}
(HERE/'prepare-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if p.resolved_request is not None and p.execution_binding is not None:
 (HERE/'resolved-request.json').write_text(json.dumps(plain(p.resolved_request),ensure_ascii=False,indent=2)+'\n')
 (HERE/'provider-preview.json').write_text(json.dumps(plain(runtime.preview(p)),ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'executable':p.resolved_request is not None and p.execution_binding is not None,'decision':p.decision.disposition,'video_calls':0},ensure_ascii=False))
