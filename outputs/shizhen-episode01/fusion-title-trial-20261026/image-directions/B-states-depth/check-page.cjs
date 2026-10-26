const {chromium}=require('/home/reggie/.npm/_npx/e78b33305587cb7c/node_modules/playwright');
const fs=require('fs');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:'/home/reggie/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome',args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];
page.on('pageerror',e=>errors.push(String(e)));
await page.goto('http://127.0.0.1:8876/outputs/shizhen-episode01/fusion-title-trial-20261026/image-directions/B-states-depth/index.html');
const results=[];
for(let i=0;i<4;i++){
await page.locator('#steps button').nth(i).click();
await page.waitForFunction(()=>{let im=document.querySelector('#hero');return im.complete&&im.naturalWidth>0});
results.push(await page.locator('#hero').evaluate(im=>({src:im.getAttribute('src'),width:im.naturalWidth,height:im.naturalHeight})));
}
await page.screenshot({path:__dirname+'/page-check.png'});
fs.writeFileSync(__dirname+'/page-check.json',JSON.stringify({errors,states:results,scope:'static image loading and navigation; not motion or artistic acceptance'},null,2));
await browser.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
