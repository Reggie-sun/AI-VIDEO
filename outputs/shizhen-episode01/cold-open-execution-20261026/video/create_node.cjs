const fs=require('node:fs'); const path=require('node:path');
const {chromium}=require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
const {createSession}=require(process.cwd()+'/src/ai_video/production/jimeng_browser.cjs');
(async()=>{
 const dir=__dirname, profile=JSON.parse(fs.readFileSync(process.cwd()+'/runs/shizhen-episode01-jimeng25-20261025-001/S02-execution/S02-profile.json'));
 const out=path.join(dir,'CO-A1-profile.json'), intent=path.join(dir,'CO-A1-node-intent.json');
 if(fs.existsSync(out)||fs.existsSync(intent))throw Error('Prior node mutation exists; inspect rather than repeat');
 const port=fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort','utf8').split('\n')[0];
 const browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);let session;
 try{
  const pages=browser.contexts().flatMap(c=>c.pages()).filter(p=>p.url()==='https://jimeng.jianying.com/ai-tool/ai-canvas/'+profile.project_id);
  if(pages.length!==1)throw Error('Exact canvas missing or ambiguous');const page=pages[0];
  session=await page.evaluateHandle(createSession,profile);await session.evaluate(s=>s.check());
  fs.writeFileSync(intent,JSON.stringify({authorization:'用户：开始做吧',project_id:profile.project_id,account_sha256:profile.account_sha256,operation:'add_one_empty_video_node_for_cold_open_CO-A1',generation_POSTs:0,issued_at:new Date().toISOString()})+'\n',{flag:'wx'});
  const node=await page.evaluate(async s=>{const o=await s.check();const api=o.canvas.mutableFeaturesApi.canvas;const before=new Set(api.getNodeIds());await api.actions.addVideoNode.execute();await s.check();const added=api.getNodeIds().filter(id=>!before.has(id));if(added.length!==1)throw Error('Ambiguous added nodes');return api.getObjectSnapshot(added[0]);},session);
  if(node.type!=='video'||node.data?.resourceId)throw Error('New node not empty');
  fs.writeFileSync(out,JSON.stringify({...profile,node_id:node.id,input_mode:'first_last_frame',duration_seconds:8,benefit_amount:8,credit_upper_bound:1500},null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({created_node:node.id,project_id:profile.project_id,input_mode:'first_last_frame',duration_seconds:8,resolution:'1080p',generation_POSTs:0}));
 }finally{if(session)await session.dispose();await browser.close();}
})().catch(e=>{console.log(JSON.stringify({status:'STOP',error_type:e.name,reason:'Node action not confirmed; no automatic mutation retry'}));process.exitCode=2;});
