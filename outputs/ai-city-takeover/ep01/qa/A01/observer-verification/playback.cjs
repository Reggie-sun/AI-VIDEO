'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const puppeteer = require(path.resolve('node_modules/puppeteer-core'));
const root = __dirname;
const raw = path.resolve('outputs/ai-city-takeover/ep01/generation/project/state/video-generation/fetch/files/65f17d6860cbde39df398f42138149a7b4fc7a0bda7fdd96952b88134a0601d5.mp4');
const sha = crypto.createHash('sha256').update(fs.readFileSync(raw)).digest('hex');
const profile = path.join(root, 'owned-temporary-browser-profile');
if (fs.existsSync(profile)) throw Error('Temporary profile already exists');
(async () => {
 let browser;
 try {
  browser = await puppeteer.launch({executablePath:'/usr/bin/google-chrome-stable',headless:true,
   userDataDir:profile,args:['--no-sandbox','--disable-background-networking','--disable-component-update','--disable-sync']});
  const page = await browser.newPage();
  await page.setViewport({width:1280,height:720});
  await page.goto('http://127.0.0.1:8767/ep01/',{waitUntil:'domcontentloaded'});
  await page.setContent('<html><body style="margin:0;background:#000"><video id="qa" muted playsinline style="width:100vw;height:100vh;object-fit:contain" src="http://127.0.0.1:8767/ep01/shots/A01-v1.mp4"></video></body></html>');
  const observed = await page.evaluate(async () => {
   const video = document.querySelector('video');
   if(video.readyState < 1) await new Promise((resolve,reject)=>{video.onloadedmetadata=resolve;video.onerror=()=>reject(Error('Metadata load failed'));});
   video.playbackRate=1; video.currentTime=0;
   const presented=[], stills=[];let nextSample=0;
   const canvas=document.createElement('canvas');canvas.width=960;canvas.height=540;
   const ctx=canvas.getContext('2d');
   let ended=false;
   const capture=(now,meta)=>{
    presented.push({mediaTime:meta.mediaTime,presentedFrames:meta.presentedFrames});
    if(meta.mediaTime>=nextSample){ctx.drawImage(video,0,0,960,540);stills.push({mediaTime:meta.mediaTime,jpeg:canvas.toDataURL('image/jpeg',0.9)});nextSample+=0.5;}
    if(!ended)video.requestVideoFrameCallback(capture);
   };
   video.requestVideoFrameCallback(capture);
   const started=performance.now();
   const done=new Promise((resolve,reject)=>{video.onended=()=>{ended=true;resolve();};video.onerror=()=>reject(Error('Playback decode failed'));});
   await video.play();await done;
   const quality=video.getVideoPlaybackQuality();
   return {duration:video.duration,currentTime:video.currentTime,playbackRate:video.playbackRate,muted:video.muted,
    wallSeconds:(performance.now()-started)/1000,ended:video.ended,error:video.error,
    quality:{totalVideoFrames:quality.totalVideoFrames,droppedVideoFrames:quality.droppedVideoFrames,corruptedVideoFrames:quality.corruptedVideoFrames},presented,stills};
  });
  for(let i=0;i<observed.stills.length;i++)fs.writeFileSync(path.join(root,`playback-${String(i).padStart(2,'0')}-${observed.stills[i].mediaTime.toFixed(3)}.jpg`),Buffer.from(observed.stills[i].jpeg.split(',')[1],'base64'));
  const sampleTimes=observed.stills.map(x=>x.mediaTime);delete observed.stills;
  const result={source_sha256:sha,source_url:'http://127.0.0.1:8767/ep01/shots/A01-v1.mp4',scope:'technical normal-speed muted playback; not human listening or acceptance',...observed,sampleTimes};
  fs.writeFileSync(path.join(root,'normal-speed-playback.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({ended:result.ended,wallSeconds:result.wallSeconds,rate:result.playbackRate,quality:result.quality,callbackCount:result.presented.length,sampleCount:sampleTimes.length}));
 } finally {
  if(browser)await browser.close();
  if(fs.existsSync(profile))fs.rmSync(profile,{recursive:true});
 }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
