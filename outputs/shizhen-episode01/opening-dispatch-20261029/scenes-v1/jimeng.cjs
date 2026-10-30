'use strict';
// Usage: node jimeng.cjs <readonly|create> <SHOT> <input_mode> <duration_seconds>
// readonly: quote only (no upload, no POST). create: one empty node + sealed profile, never twice.
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
const {createSession,buildVideoAction}=require(path.resolve('src/ai_video/production/jimeng_browser.cjs'));
const [cmd,shot,inputMode,durationText]=process.argv.slice(2);
const out=path.join(__dirname,shot);
const prior=JSON.parse(fs.readFileSync('outputs/shizhen-episode01/macro-opening-video-20261027/MC01-02-1080p-v3/profile.json'));
const duration=Number(durationText);
if(!['readonly','create'].includes(cmd)||!fs.existsSync(out)||!['multimodal','first_frame','first_last_frame'].includes(inputMode)||!Number.isInteger(duration))throw Error('bad arguments');
const MODEL='seedance_2.0_vip',RES='1080p',MODE_NO={multimodal:4,first_frame:2,first_last_frame:3}[inputMode];
const base={model_id:MODEL,input_mode:inputMode,account_sha256:prior.account_sha256,project_id:prior.project_id,duration_seconds:duration,resolution:RES,aspect_ratio:'16:9',benefit_amount:duration};
const materials=inputMode==='multimodal'?[{kind:'image'}]:inputMode==='first_frame'?[{kind:'image',image_role:'first_frame'}]:[{kind:'image',image_role:'first_frame'},{kind:'image',image_role:'last_frame'}];
(async()=>{
  const port=fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort','utf8').split('\n')[0];
  if(!/^\d{2,5}$/.test(port))throw Error('Configured CDP endpoint unavailable');
  const b=await chromium.connectOverCDP('http://127.0.0.1:'+port);
  try{
    const pages=b.contexts().flatMap(c=>c.pages()).filter(p=>p.url()==='https://jimeng.jianying.com/ai-tool/ai-canvas/'+prior.project_id);
    if(pages.length!==1)throw Error('Exact canvas missing or ambiguous');
    const s=await pages[0].evaluateHandle(createSession,prior);
    if(cmd==='readonly'){
      const action=buildVideoAction(base,materials);
      const r=await s.evaluate(async(s,[action,model,modeNo])=>{
        const o=await s.check();const store=o.canvas.generationRuntime.videoGenerationConfigStore;
        const commerce=store.service.source.commerceConfig.modelConfig[model];const benefitStrings=[];
        (function scan(v,p){if(typeof v==='string'&&v.startsWith('seedance'))benefitStrings.push({path:p,value:v});else if(v&&typeof v==='object')for(const [k,x] of Object.entries(v))scan(x,p+'.'+k);})(commerce,'modelConfig.'+model);
        const quote=o.client.quoteActions([{id:'dispatch-readonly',action}]);const state=o.client.getActionState(action);
        const credit=o.client.getSnapshot().data?.localCredit;
        return {account_verified:true,mode:store.getModeConfig(model,modeNo),benefitStrings,quote:{status:quote.status,credits:quote.credits},
          state_status:state.status,local_credit:credit,sufficient_balance:Number.isSafeInteger(credit)&&credit>=quote.credits,action};
      },[action,MODEL,MODE_NO]);
      fs.writeFileSync(path.join(out,'native-readonly.json'),JSON.stringify({created_at:new Date().toISOString(),...r,generation_POSTs:0,uploads:0},null,2)+'\n');
      console.log(JSON.stringify({shot,quote:r.quote,status:r.state_status,local_credit:r.local_credit,benefits:r.benefitStrings.filter(x=>x.path.includes(RES)).map(x=>x.value)}));
    }else{
      if(fs.existsSync(path.join(out,'node-create-intent.json')))throw Error('Existing node intent; inspect instead of retry');
      const ro=JSON.parse(fs.readFileSync(path.join(out,'native-readonly.json')));
      const benefit=ro.benefitStrings.find(x=>x.path.endsWith('.'+RES+'.benefitType')||x.path.includes('resolutionBenefitKeys.'+RES+'.benefitType'));
      if(!benefit)throw Error('Benefit for resolution not found in readonly config');
      const before=await s.evaluate(async s=>{const o=await s.check();return o.canvas.mutableFeaturesApi.canvas.getNodeIds();});
      fs.writeFileSync(path.join(out,'node-create-intent.json'),JSON.stringify({authorization_quote:'先把画面做出来',operation:'add_one_empty_video_node',project_id:prior.project_id,account_sha256:prior.account_sha256,before_node_ids:before,created_at:new Date().toISOString(),generation_POSTs:0},null,2)+'\n',{flag:'wx'});
      const node=await s.evaluate(async(s,before)=>{const o=await s.check(),api=o.canvas.mutableFeaturesApi.canvas;await api.actions.addVideoNode.execute();await s.check();const ids=api.getNodeIds().filter(id=>!before.includes(id));if(ids.length!==1)throw Error('Ambiguous new node');const n=api.getObjectSnapshot(ids[0]);if(n.type!=='video'||n.data?.resourceId)throw Error('Node is not empty video');return {node_id:n.id,node_type:n.type,empty:true};},before);
      fs.writeFileSync(path.join(out,'node-created.json'),JSON.stringify({...node,project_id:prior.project_id,account_sha256:prior.account_sha256,generation_POSTs:0},null,2)+'\n',{flag:'wx'});
      const profile={...base,node_id:node.node_id,benefit_type:benefit.value,credit_upper_bound:1500};
      fs.writeFileSync(path.join(out,'profile.json'),JSON.stringify(profile,null,2)+'\n',{flag:'wx'});
      console.log(JSON.stringify({shot,node_id:node.node_id,benefit_type:benefit.value,generation_POSTs:0}));
    }
    await s.dispose();
  }finally{await b.close();}
})().catch(e=>{console.log(JSON.stringify({STOP:true,shot,type:e.name,reason:e.message.slice(0,200),do_not_retry:true}));process.exitCode=2;});
