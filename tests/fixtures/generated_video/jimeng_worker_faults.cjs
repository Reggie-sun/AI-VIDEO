'use strict';
// Execute the shipped Worker in a browser-like realm; no real Provider calls.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const workerPath = process.argv[2];
const protocol = process.argv[3].startsWith('protocol_');
const scenario = protocol ? process.argv[3].slice('protocol_'.length) : process.argv[3];
const profile = {account_sha256: crypto.createHash('sha256').update('account-a').digest('hex'),
  project_id:'f0ed223b-090e-4ed6-b394-283f8b7dbd07',node_id:'node_bq6wajb5xe',
  model_id:'seedance_2.5',resolution:'720p',duration_seconds:5,
  credit_upper_bound:30,benefit_amount:5,benefit_type:'seedance_25_720p_output'};
const materials=[{index:0,kind:'image',asset_id:'fault-image',asset_sha256:'a'.repeat(64),
  size_bytes:1,storage_id:'fixture-image'}];
const params={mode:4,model_name:profile.model_id,aspect_ratio:'16:9',resolution:'720p',
  duration_ms:5000,prompt:'fixture {{image:0}}',materials:[{type:2,image_uri:'fixture-image'}],
  meta_list:[{type:1,text:'fixture '},{type:2,material_idx:0}]};
const ids={submit_id:'cedcb4bc-5bb5-4c8e-9c10-278f4f388518',resource_id:'71949d15-dac1-4642-b83c-24f238650876'};
const timers=[];
let resolveNative, foreignEnvelope, calls=0, exposed={}, routes=[];
const node={type:'video',data:{generationDraft:null}};
const httpProto={postEnvelope:async(path,body)=>browser.window.fetch(path,{method:'POST',body:JSON.stringify(body)})};
const http=Object.create(httpProto);
const client={quoteActions:()=>({status:'available',credits:30}),
  getActionState:()=>({status:'allowed',quote:{credits:30}}),
  getSnapshot:()=>({data:{localCredit:100}})};
const canvas={controller:{},actions:{projectId:profile.project_id},
  mutableFeaturesApi:{canvas:{getObjectSnapshot:()=>node,actions:{setNodeGenerationDraft:{
    execute:async(_,draft,{canCommit})=>{assert(canCommit());node.data.generationDraft=draft;return {ok:true};}}}}},
  generationRuntime:{videoGenerationConfigStore:{validate:()=>({status:'valid'})},actions:{
    getVideoSubmissionSnapshot:()=>({state:'idle',acceptedResourceIds:[]}),
    submitVideo:()=>new Promise(resolve=>{resolveNative=resolve;})}}};
let account={uid:'account-a'};
const elements=()=>[canvas,{client},{endpoints:{http}},account].map(value=>({
  __reactFiber$test:{memoizedProps:{value},return:null}}));
const browser=vm.createContext({window:{},location:{href:'https://jimeng.jianying.com/ai-tool/ai-canvas/'+profile.project_id,origin:'https://jimeng.jianying.com'},
  document:{querySelectorAll:elements},crypto:crypto.webcrypto,TextEncoder,URL,Date,
  setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout:()=>{},
  fetch:async(url,init)=>{
    if(String(url).includes('/node_generate')) {
      const body=JSON.parse(init.body);
      if(routes.length) await routes[0]({request:()=>({postDataJSON:()=>body,method:()=>init.method}),
        continue:async()=>{calls++;},abort:async()=>{throw Error('route blocked');}});
      else calls++;
    }
    return {ok:true,json:async()=>({ret:0,data:{resources:[{...ids,task_id:'123',status:200,video:{gen:params}}]}})};
  },
  AbortSignal,console});
vm.runInContext('window.fetch=fetch',browser);
const page={
  evaluate:async(fn,arg)=>{browser.__arg=arg;return vm.runInContext('('+fn.toString()+')(__arg)',browser);},
  evaluateHandle:async(fn,arg)=>{const value=await page.evaluate(fn,arg);return {
    _value:value,evaluate:async(f,a)=>f(value,a),dispose:async()=>{}};},
  exposeFunction:async(name,fn)=>{exposed[name]=fn;browser.window[name]=fn;if(scenario==='binding_unavailable') return undefined;return {dispose:async()=>{delete exposed[name];delete browser.window[name];}};},
  route:async(pattern,fn)=>{routes.push(fn);},unroute:async()=>{routes=[];},
  waitForTimeout:async()=>{if(scenario.startsWith('timeout_late_')) timers.forEach(fn=>fn()); else await new Promise(resolve=>setTimeout(resolve,1));},
};
// JSHandles are represented by realm values for this transport-only fixture.
const originalEvaluate=page.evaluate;
page.evaluate=async(fn,arg)=>{
  const unhandle=x=>x?._value||x;
  if(arg&&typeof arg==='object') arg=Object.fromEntries(Object.entries(arg).map(([k,v])=>[k,unhandle(v)]));
  return originalEvaluate(fn,arg);
};
const fixtureRequire=id=>id==='node:readline'?{createInterface:()=>({[Symbol.asyncIterator]:()=>({next:async()=>({
  done:false,value:JSON.stringify({approved:scenario!=='host_reject'})})})})}:require(id);
const host=vm.createContext({require:fixtureRequire,module:{exports:{}},process:{stdin:process.stdin,stdout:{write:()=>{
  if(scenario==='after_approval_identity_drift') account={uid:'account-b'};
  if(scenario==='quote_change') client.getSnapshot=()=>({data:{localCredit:0}});
}}},
  Buffer,setTimeout,clearTimeout,console});
vm.runInContext(fs.readFileSync(workerPath,'utf8')+'\nmodule.exports.__submit=submit; module.exports.__connect=connect;',host);
const {__submit:submit,__connect:connect}=host.module.exports;
async function runWorkerProtocol() {
  // Run the actual executable entry/catch, not a copy of its classifier.
  const frames=[];
  let finish, reads=0;
  const finished=new Promise(resolve=>{finish=resolve;});
  const fakeProcess={stdin:{destroy:()=>finish()},stdout:{write:line=>frames.push(JSON.parse(line))}};
  const fakeBrowser={contexts:()=>[{pages:()=>[{...page,url:()=>browser.location.href}]}],close:async()=>{}};
  const command={operation:'submit',profile,video_params:params,materials,
    profile_dir:'/fixture',playwright_module:'fixture-playwright'};
  const runRequire=id=>id==='node:readline'?{createInterface:()=>({[Symbol.asyncIterator]:()=>({
    next:async()=>({done:false,value:JSON.stringify(reads++===0?command:{approved:scenario!=='host_reject'})})})})}:
    id==='node:fs'?{...fs,readFileSync:()=> '9222\n'}:
    id==='fixture-playwright'?{chromium:{connectOverCDP:async()=>fakeBrowser}}:require(id);
  const runModule={exports:{}};runRequire.main=runModule;
  const runHost=vm.createContext({require:runRequire,module:runModule,process:fakeProcess,
    Buffer,setTimeout,clearTimeout,console});
  vm.runInContext(fs.readFileSync(workerPath,'utf8'),runHost);
  await finished;
  const terminal=frames.at(-1);
  const proven=['mutated_request','quote_precondition_changed'].includes(scenario);
  assert.equal(terminal.ok,false);
  assert.equal(terminal.no_effect,proven,JSON.stringify({scenario,frames,calls}));
  assert.equal(calls,scenario==='response_lost'?1:0);
  assert.equal(frames.filter(x=>x.event==='dispatch').length,
    ['response_lost','host_reject'].includes(scenario)?1:0);
  assert.equal(fakeProcess.exitCode,1);
  assert(!JSON.stringify(frames).includes('PRIVATE_ERROR_PAYLOAD'));
  if(proven){
    // A native continuation detached from its promise must remain fenced too.
    assert.equal(browser.window.__aiVideoJimengFence.closed,true);
    await assert.rejects(http.postEnvelope('/octo_api/v1/node_generate',{
      initial:{node_id:profile.node_id}},{}));
    await assert.rejects(browser.window.fetch('/octo_api/v1/node_generate',{
      method:'POST',body:JSON.stringify({initial:{node_id:profile.node_id}})}));
    assert.equal(calls,0);
  }
}
async function session(){
  if(!host.module.exports.createSession) return undefined;
  return page.evaluateHandle(host.module.exports.createSession,profile);
}
async function main(){
  if(scenario==='ambiguous_page'){
    const fakeBrowser={contexts:()=>[{pages:()=>[{url:()=>browser.location.href},{url:()=>browser.location.href}]}],close:async()=>{calls++;}};
    const r=host.require;host.require=id=>id==='fixture-playwright'?{chromium:{connectOverCDP:async()=>fakeBrowser}}:
      id==='node:fs'?{readFileSync:()=> '9222\n'}:r(id);
    // require is resolved at call time; Worker fs binding needs its own stub.
    const freshHost=vm.createContext({...host,module:{exports:{}}});
    vm.runInContext(fs.readFileSync(workerPath,'utf8')+'\nmodule.exports.__connect=connect;',freshHost);
    await assert.rejects(freshHost.module.exports.__connect({profile,profile_dir:'/fixture',playwright_module:'fixture-playwright'}));
    assert.equal(calls,1);return;
  }
  if(scenario==='identity_drift'){
    const s=await session();assert(s,'session guard missing');
    account={uid:'account-b'};
    await assert.rejects(s.evaluate(x=>x.check()));assert.equal(calls,0);return;
  }
  const s=await session();
  if(scenario==='preflight_cleanup') canvas.generationRuntime.videoGenerationConfigStore.validate=()=>({status:'invalid'});
  if(['native_no_quote','success','duplicate_post','host_reject','after_approval_identity_drift','quote_change','mutated_request','quote_precondition_changed','duplicate_wire','replaced_http','response_lost','guard_rejection_pending','guard_rejection_owner_changed','guard_rejection_instance_changed','guard_rejection_account_changed','unknown_native_error'].includes(scenario)){
    canvas.generationRuntime.actions.submitVideo=async()=>{
      if(scenario==='unknown_native_error')throw Error('PRIVATE_ERROR_PAYLOAD');
      const body={project_id:profile.project_id,op:1,initial:{node_id:profile.node_id,...ids,
        items:[{resource_id:ids.resource_id,type:2,params:{video_params:params},commerce_selection:{benefit_type:profile.benefit_type,quote_precondition:{expected_benefit_amount:5,expected_credits_amount:30}}}]}};
      if(scenario==='native_no_quote') delete body.initial.items[0].commerce_selection.quote_precondition;
      if(scenario==='quote_precondition_changed') body.initial.items[0].commerce_selection.quote_precondition.expected_credits_amount=31;
      if(scenario==='mutated_request') body.initial.items[0].params.video_params={...params,resolution:'480p'};
      if(['guard_rejection_pending','guard_rejection_owner_changed','guard_rejection_instance_changed','guard_rejection_account_changed'].includes(scenario)){
        body.initial.items[0].params.video_params={...params,resolution:'480p'};
        await assert.rejects(http.postEnvelope('/octo_api/v1/node_generate',body,{}));
        if(scenario==='guard_rejection_owner_changed'){
          httpProto.postEnvelope=async()=>{throw Error('PRIVATE_ERROR_PAYLOAD');};
          return {status:'error'};
        }
        if(scenario==='guard_rejection_instance_changed'){
          http.postEnvelope=async()=>{throw Error('PRIVATE_ERROR_PAYLOAD');};
          return {status:'error'};
        }
        if(scenario==='guard_rejection_account_changed'){
          account={uid:'account-b'};
          return {status:'error'};
        }
        return new Promise(resolve=>{resolveNative=resolve;});
      }
      if(scenario==='replaced_http') {foreignEnvelope=async()=>browser.window.fetch('/octo_api/v1/node_generate',{method:'POST',body:JSON.stringify(body)});httpProto.postEnvelope=foreignEnvelope;}
      await http.postEnvelope('/octo_api/v1/node_generate',body,{});
      if(scenario==='response_lost')throw Error('PRIVATE_ERROR_PAYLOAD');
      if(scenario==='duplicate_wire') await assert.rejects(browser.window.fetch('/octo_api/v1/node_generate',{method:'POST',body:JSON.stringify(body)}));
      if(scenario==='duplicate_post') await assert.rejects(http.postEnvelope('/octo_api/v1/node_generate',body,{}));
      return {status:'success'};
    };
  }
  if(protocol){await runWorkerProtocol();return;}
  const submitting=submit(page,{profile,video_params:params,materials},s);
  submitting.catch(()=>{});
  if(scenario==='binding_unavailable'){
    await assert.rejects(submitting);assert.equal(calls,0);
    assert.equal(browser.window.__aiVideoJimengFence,null);
    assert.equal(Object.keys(browser.window).filter(k=>k.startsWith('__aiVideoJimengAdmit_')).length,0);return;
  }
  if(['native_no_quote','success','duplicate_post','duplicate_wire'].includes(scenario)){
    const result=await submitting;assert.equal(result.resource_id,ids.resource_id);
    assert.equal(calls,1);assert.equal(routes.length,0);assert.equal(Object.keys(exposed).length,0);
    assert.equal(browser.window.__aiVideoJimengFence,null);return;
  }
  if(['host_reject','after_approval_identity_drift','quote_change','mutated_request','preflight_cleanup','quote_precondition_changed','replaced_http'].includes(scenario)){
    await assert.rejects(submitting);assert.equal(calls,0);
    if(['mutated_request','quote_precondition_changed'].includes(scenario))
      assert.equal(browser.window.__aiVideoJimengFence.closed,true);
    else assert.equal(browser.window.__aiVideoJimengFence,null);
    assert.equal(Object.keys(exposed).length,0);assert.equal(routes.length,0);
    if(scenario==='replaced_http') assert.equal(httpProto.postEnvelope,foreignEnvelope);
    return;
  }
  if(scenario==='concurrent'){
    // Wait for the first native invocation, not a timing-only sleep.
    while(!resolveNative) await new Promise(resolve=>setImmediate(resolve));
    await assert.rejects(submit(page,{profile,video_params:params,materials},await session()));
    resolveNative({status:'error'});await assert.rejects(submitting);return;
  }
  if(scenario.startsWith('timeout_late_')){
    await assert.rejects(submitting);
    const body={project_id:profile.project_id,op:1,initial:{node_id:profile.node_id,...ids,
      items:[{resource_id:ids.resource_id,type:2,params:{video_params:params},commerce_selection:{benefit_type:profile.benefit_type,quote_precondition:{expected_benefit_amount:5,expected_credits_amount:30}}}]}};
    if(scenario==='timeout_late_fetch') {
      for(const url of ['/octo_api/v1/node_generate',new URL('/octo_api/v1/node_generate',browser.location.href)])
        await assert.rejects(browser.window.fetch(url,{method:'POST',body:JSON.stringify(body)}));
    }
    else {
      if(scenario==='timeout_late_replaced_http') httpProto.postEnvelope=async()=>browser.window.fetch('/octo_api/v1/node_generate',{method:'POST',body:JSON.stringify(body)});
      await assert.rejects(http.postEnvelope('/octo_api/v1/node_generate',body,{}));
    }
    assert.equal(calls,0,'expired native continuation reached original HTTP method');
    if(resolveNative) resolveNative({status:'error'});return;
  }
  throw Error('unknown scenario');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
