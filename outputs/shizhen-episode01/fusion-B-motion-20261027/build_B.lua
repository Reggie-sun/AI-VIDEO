-- Local single-shot compositor. Final timeline and sound remain in HyperFrames.
local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local plates='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-title-trial-20261026/source-frames'
local pm=resolve:GetProjectManager();local p=assert(pm:GetCurrentProject());assert(p:GetName()=='Shizhen-B-Layered-20261027')
local item=assert(p:GetCurrentTimeline():GetItemListInTrack('video',1)[1]);local c=assert(item:GetFusionCompByIndex(1))
assert(not c:FindTool('OriginalMovingPlate'),'Existing production graph: inspect before rerun')
c:SetAttrs({COMPN_GlobalStart=0,COMPN_GlobalEnd=71,COMPN_RenderStart=0,COMPN_RenderEnd=71})
c:SetPrefs({['Comp.FrameFormat.Width']=1920,['Comp.FrameFormat.Height']=1080,['Comp.FrameFormat.Rate']=24})
c:Lock()
-- Disconnected diagnostic probes are retained; no unsupported deletion API.
local function node(id,name,x,y) local t=assert(c:AddTool(id,x,y),id);t:SetAttrs({TOOLS_Name=name});return t end
local function set(t,k,v) t:SetInput(k,v) end
local function expr(t,k,v) t[k]:SetExpression(v) end
local plate=node('Loader','OriginalMovingPlate',0,0);plate.Clip=plates..'/plate_0000.png'
plate:SetAttrs({TOOLNT_Clip_Start={0},TOOLNT_Clip_End={71}})

-- Density changes follow image luminance. The spatial region never travels.
local tone=node('Custom','PhotographicDensity',2,0);tone.Image1=plate.Output
expr(tone,'NumberIn1','min(1,max(0,(time-3)/17))')
expr(tone,'NumberIn2','min(1,max(0,(time-12)/25))')
set(tone,'Intermediate1','0.2126*r1+0.7152*g1+0.0722*b1')
set(tone,'Intermediate2','min(1,max(0,(r1-b1)*5))*min(1,max(0,(i1-0.42)*4))')
set(tone,'Intermediate3','0.96-0.40*sqrt(max(0,i1))')
set(tone,'Intermediate4','n2*min(1,max(0,(0.67-i1)*4.5))*0.87')
for _,v in ipairs({{'RedExpression','r1',0.985},{'GreenExpression','g1',0.993},{'BlueExpression','b1',1.0}}) do
 set(tone,v[1],'('..v[2]..'*(1-n1)+i1*n1)*(1-i4)+(i3*'..v[3]..'*(1-i2)+'..v[2]..'*i2)*i4')
end
set(tone,'AlphaExpression','a1')
local region=node('RectangleMask','FixedVacantSpace',1,3)
set(region,'Center',{0.254,0.50});set(region,'Width',0.54);set(region,'Height',1.12);set(region,'SoftEdge',0.035)
local density=node('Merge','DevelopEmptySpace',4,0);density.Background=plate.Output;density.Foreground=tone.Output;density.EffectMask=region.Mask

local title=node('Loader','IsolatedTitleMaster',0,6);title.Clip=root..'/title-layer.png'
local fit=node('BetterResize','MatchPlateRaster',2,6);fit.Input=title.Output;set(fit,'Width',1920);set(fit,'Height',1080)
local place=node('Transform','FixedTitlePlacement',4,6);place.Input=fit.Output;set(place,'Size',0.72);set(place,'Center',{0.3136,0.5752})
local ink=node('Custom','LatentSilverInk',6,5);ink.Image1=place.Output;ink.Image2=plate.Output
expr(ink,'NumberIn1','min(1,max(0,(time-20)/24))')
set(ink,'Intermediate1','0.2126*r2+0.7152*g2+0.0722*b2')
set(ink,'Intermediate2','min(1,max(0,(n1-(0.08+0.40*i1))*6))')
set(ink,'Intermediate3','a1*i2*(0.97-min(0.16,max(0,(i1-0.55)*0.6)))')
set(ink,'RedExpression','(0.018+0.045*i1)*i3');set(ink,'GreenExpression','(0.021+0.045*i1)*i3');set(ink,'BlueExpression','(0.023+0.045*i1)*i3');set(ink,'AlphaExpression','i3')
local clean=node('RectangleMask','GlyphOnlyArea',5,8);set(clean,'Center',{0.23,0.55});set(clean,'Width',0.43);set(clean,'Height',0.95);set(clean,'SoftEdge',0)
local reveal=node('Merge','TitleAndLivingRain',8,0);reveal.Background=density.Output;reveal.Foreground=ink.Output;reveal.EffectMask=clean.Mask

-- Actual foreground mullions and AI source mark remain from the moving plate.
local latest=reveal
for i,v in ipairs({{0.178,0.55,0.015,0.84},{0.3905,0.52,0.006,0.86},{0.051,0.951,0.099,0.095}}) do
 local m=node('RectangleMask','SourceProtection'..i,8,i+8);set(m,'Center',{v[1],v[2]});set(m,'Width',v[3]);set(m,'Height',v[4]);set(m,'SoftEdge',0.001)
 local merge=node('Merge','KeepOriginalLayer'..i,8+i*2,0);merge.Background=latest.Output;merge.Foreground=plate.Output;merge.EffectMask=m.Mask;latest=merge
end
local out=assert(c:FindTool('MediaOut1'));out.Input=latest.Output
local saver=node('Saver','BMotionFrames',16,0);saver.Input=latest.Output;saver.Clip=root..'/render-B1/title_0000.png';set(saver,'OutputFormat','PNGFormat')
c:Unlock();assert(pm:SaveProject());assert(item:ExportFusionComp(root..'/B1.comp',1));print('B_GRAPH_READY')
for _,f in ipairs({0,16,28,42,60,71}) do print('B_STILL',f,tostring(c:Render({Start=f,End=f,Wait=true,HiQ=true,Tool=saver}))) end
print('B_STILLS_DONE')
