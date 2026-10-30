'use strict';
// One empty node only; no upload or generation. Re-run is prohibited by intent file.
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
const {createSession}=require(path.resolve('src/ai_video/production/jimeng_browser.cjs'));
const prior=JSON.parse(fs.readFileSync('outputs/shizhen-episode01/macro-opening-video-20261027/MC03-descent-v1/profile.json'));
const out=__dirname;
if(fs.existsSync(path.join(out,'node-create-intent.json')))throw Error('Existing node intent; inspect instead of retry');
(async()=>{
  const port=fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort','utf8').split('\n')[0];
  if(!/^\d{2,5}$/.test(port))throw Error('Configured CDP endpoint unavailable');
  const b=await chromium.connectOverCDP('http://127.0.0.1:'+port);
  try{
    const pages=b.contexts().flatMap(c=>c.pages()).filter(p=>p.url()==='https://jimeng.jianying.com/ai-tool/ai-canvas/'+prior.project_id);
    if(pages.length!==1)throw Error('Exact canvas missing or ambiguous');
    const s=await pages[0].evaluateHandle(createSession,prior);
    const before=await s.evaluate(async s=>{const o=await s.check();return o.canvas.mutableFeaturesApi.canvas.getNodeIds();});
    fs.writeFileSync(path.join(out,'node-create-intent.json'),JSON.stringify({authorization_quote:'直接重做,生圖調用codex',operation:'add_one_empty_video_node',project_id:prior.project_id,account_sha256:prior.account_sha256,before_node_ids:before,created_at:new Date().toISOString(),generation_POSTs:0},null,2)+'\n',{flag:'wx'});
    const node=await s.evaluate(async(s,before)=>{const o=await s.check(),api=o.canvas.mutableFeaturesApi.canvas;await api.actions.addVideoNode.execute();await s.check();const ids=api.getNodeIds().filter(id=>!before.includes(id));if(ids.length!==1)throw Error('Ambiguous new node');const n=api.getObjectSnapshot(ids[0]);if(n.type!=='video'||n.data?.resourceId)throw Error('Node is not empty video');return {node_id:n.id,node_type:n.type,empty:true};},before);
    fs.writeFileSync(path.join(out,'node-created.json'),JSON.stringify({...node,project_id:prior.project_id,account_sha256:prior.account_sha256,generation_POSTs:0},null,2)+'\n',{flag:'wx'});
    const profile={model_id:'seedance_2.5',input_mode:'first_last_frame',account_sha256:prior.account_sha256,project_id:prior.project_id,node_id:node.node_id,duration_seconds:16,resolution:'480p',aspect_ratio:'16:9',benefit_amount:16,benefit_type:'seedance_25_480p_no_input_video_output',credit_upper_bound:1500};
    const config=JSON.parse(fs.readFileSync(path.join(out,'native-readonly.json')));
    if(!config.benefitStrings.some(x=>x.path==='modelConfig.seedance_2.5.videoResolutionPriceConfigs.480p.noInputVideoPrice.benefitType'&&x.value===profile.benefit_type))throw Error('Benefit differs from current config');
    fs.writeFileSync(path.join(out,'profile.json'),JSON.stringify(profile,null,2)+'\n',{flag:'wx'});
    await s.dispose();console.log(JSON.stringify({node_id:node.node_id,empty:true,generation_POSTs:0,profile_saved:true}));
  }finally{await b.close();}
})().catch(e=>{console.log(JSON.stringify({STOP:true,type:e.name,reason:e.message.slice(0,180),do_not_retry:true}));process.exitCode=2;});
