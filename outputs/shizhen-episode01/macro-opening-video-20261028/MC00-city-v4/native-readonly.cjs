'use strict';
// Read only the exact configured account/canvas through the existing owner.
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('/home/reggie/.local/share/ai-video/playwright-mcp/node_modules/playwright');
const {createSession,buildVideoAction} = require(path.resolve('src/ai_video/production/jimeng_browser.cjs'));
const prior = JSON.parse(fs.readFileSync('outputs/shizhen-episode01/macro-opening-video-20261027/MC03-descent-v1/profile.json'));
const profile = {...prior,model_id:'seedance_2.5',input_mode:'first_last_frame',duration_seconds:16,resolution:'480p',benefit_amount:16};
const action=buildVideoAction(profile,[{kind:'image',image_role:'first_frame'},{kind:'image',image_role:'last_frame'}]);
const dest=path.join(__dirname,'native-readonly.json');
(async()=>{
  const port=fs.readFileSync('/home/reggie/.local/share/ai-video/playwright-mcp/profile/DevToolsActivePort','utf8').split('\n')[0];
  if(!/^\d{2,5}$/.test(port))throw Error('Configured CDP endpoint unavailable');
  const browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);
  try{
    const pages=browser.contexts().flatMap(c=>c.pages()).filter(p=>p.url()==='https://jimeng.jianying.com/ai-tool/ai-canvas/'+profile.project_id);
    if(pages.length!==1)throw Error('Exact canvas missing or ambiguous');
    const session=await pages[0].evaluateHandle(createSession,profile);
    const result=await session.evaluate(async(s,action)=>{
      const o=await s.check();const store=o.canvas.generationRuntime.videoGenerationConfigStore;
      const commerce=store.service.source.commerceConfig.modelConfig['seedance_2.5'];
      const benefitStrings=[];
      function scan(v,p){if(typeof v==='string'&&v.startsWith('seedance'))benefitStrings.push({path:p,value:v});
        else if(v&&typeof v==='object')for(const [k,x]of Object.entries(v))scan(x,p+'.'+k);}
      scan(commerce,'modelConfig.seedance_2.5');
      const state=o.client.getActionState(action);const quote=o.client.quoteActions([{id:'mc00-v4-readonly',action}]);
      await s.check();
      return {account_verified:true,mode:store.getModeConfig('seedance_2.5',3),benefitStrings,
        quote:{status:quote.status,credits:quote.credits},state_status:state.status,
        activation_type:typeof state.activation,activation_keys:Object.keys(state.activation||{}),
        sufficient_balance:Number.isSafeInteger(o.client.getSnapshot().data?.localCredit)&&o.client.getSnapshot().data.localCredit>=quote.credits,
        action};
    },action);
    fs.writeFileSync(dest,JSON.stringify({created_at:new Date().toISOString(),...result,generation_POSTs:0,uploads:0},null,2)+'\n',{flag:'wx'});
    console.log(JSON.stringify({saved:dest,quote:result.quote,status:result.state_status,benefitStrings:result.benefitStrings}));
    await session.dispose();
  }finally{await browser.close();}
})().catch(e=>{console.log(JSON.stringify({STOP:true,type:e.name,reason:e.message.slice(0,180)}));process.exitCode=2;});
