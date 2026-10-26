"""Bounded task caller over the existing Suno service; no provider implementation."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, os, fcntl, subprocess, sys
from ai_video.production.music_direction import SceneMusicBrief, direct_music
from ai_video.production.suno_music import SunoMusicService, CliTransport, build_generation_argv, generation_identity, request_id_for
UNIT=Path(__file__).resolve().parent
REPO=Path.cwd()
HISTORY=REPO/'outputs/shizhen-episode01/suno-v6-music-pilot-20261026'
SOURCES=[HISTORY/x for x in ('request-01/consume.json','request-02/consume.json','manual-request-03/consume.json','cli-repair-live-04/consume.json')]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
 with (UNIT/name).open('x') as f:
  json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
briefs=json.loads((REPO/'docs/superpowers/artifacts/drama/shizhen-episode-01/cold-open-preparation/music/briefs.json').read_text())
D=direct_music(SceneMusicBrief.model_validate(next(b for b in briefs if b['cue_id']=='co-missing-response')))
class Transport(CliTransport):
 def run(self,argv,*,timeout_seconds):
  if 'generate' in argv and '--dry-run' not in argv:
   intent=json.loads((UNIT/'intent.json').read_text())
   if list(argv)!=intent['live_argv'] or intent['historical_consumption_hashes']!={str(p.relative_to(HISTORY)):digest(p) for p in SOURCES}:raise RuntimeError('Input/history changed; no submit')
   if '--no-captcha' in argv or '--force' in argv:raise RuntimeError('Forbidden bypass')
   with (HISTORY/'.execution.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    write('consume.json',{'consumed_at':datetime.now(timezone.utc).isoformat(),'intent_sha256':digest(UNIT/'intent.json'),'logical_music_request_number':5,'old_maximum':4,'new_finite_maximum':5,'new_task_remaining_after_this':0,'automatic_retries':0})
    return super().run(argv,timeout_seconds=timeout_seconds)
  return super().run(argv,timeout_seconds=timeout_seconds)
s=SunoMusicService(ledger_dir=UNIT/'service-ledger',transport=Transport('suno'))
if sys.argv[1]=='prepare':
 write('intent.json',{'authorization_quote':'开始做吧','scope':'已接受冷开场两位，缺席的应答独立原创器乐cue，一次v6生成一对候选','previous_music_consumptions':4,'new_unit_count':1,'new_total_ceiling':5,'historical_unknowns_preserved':True,'historical_consumption_hashes':{str(p.relative_to(HISTORY)):digest(p) for p in SOURCES},'generation_identity':generation_identity(D),'request_id':request_id_for(D),'live_argv':['--json','--no-browser',*build_generation_argv(D,dry_run=False)],'direction':D.model_dump(mode='json'),'egress':'Suno approved instrumental text only; no uploaded film, image or audio','budget':'task-local finite one pair; report actual credits; no purchase; no global policy modification','created_at':datetime.now(timezone.utc).isoformat()})
 r=s.dry_run(D);write('dry-run.json',r.model_dump(mode='json'));print(json.dumps({'prepared':True,'request_id':request_id_for(D),'submitted':False}))
elif sys.argv[1]=='submit':
 if (UNIT/'consume.json').exists() or (UNIT/'STOP.json').exists():raise RuntimeError('Consumed or stopped; no retry')
 try:
  r=s.submit(D,paid_generation_authorized=True);write('submit-result.json',r.model_dump(mode='json'));print(json.dumps(r.model_dump(mode='json'),ensure_ascii=False))
 except Exception as e:
  write('STOP.json',{'new_submissions_allowed':False,'type':type(e).__name__,'code':str(getattr(e,'code','UNKNOWN'))});print(json.dumps({'status':'STOP','code':str(getattr(e,'code','UNKNOWN'))}));raise SystemExit(2) from None
else:raise ValueError('prepare or submit')
