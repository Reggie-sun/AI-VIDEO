-- Shot compositor only. Existing narrative edits and audio are not modified.
local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-title-trial-20261026'
local r=assert(resolve or bmd.scriptapp('Resolve'))
local pm=r:GetProjectManager()
local name='Shizhen-Fusion-Title-Trial-20261026'
local p=pm:LoadProject(name) or pm:CreateProject(name)
assert(p,'Cannot open isolated title project')
assert(p:GetTimelineCount()==0,'Existing attempt: inspect outcome before rerunning')
p:SetSetting('timelineFrameRate','24')
p:SetSetting('timelineResolutionWidth','1920')
p:SetSetting('timelineResolutionHeight','1080')
local tl=assert(p:GetMediaPool():CreateEmptyTimeline('Title-72-Frames'))
p:SetCurrentTimeline(tl)
r:OpenPage('edit')
local item=assert(tl:InsertFusionCompositionIntoTimeline())
local c=assert(item:GetFusionCompByIndex(1))
c:SetAttrs({COMPN_GlobalStart=0,COMPN_GlobalEnd=71,COMPN_RenderStart=0,COMPN_RenderEnd=71})
c:SetPrefs({['Comp.FrameFormat.Width']=1920,['Comp.FrameFormat.Height']=1080,['Comp.FrameFormat.Rate']=24})
c:Lock()
local function node(id,name,x,y)
 local t=assert(c:AddTool(id,x,y)); t:SetAttrs({TOOLS_Name=name}); return t
end
local plate=node('Loader','OriginalRainPlate',0,0)
plate.Clip=root..'/source-frames/plate_0000.png'
plate:SetAttrs({TOOLNT_Clip_Start={0},TOOLNT_Clip_End={71}})
local zone=node('RectangleMask','EmptyPlaceExposure',0,2)
zone:SetInput('Center',{0.365,0.54});zone:SetInput('Width',0.35);zone:SetInput('Height',0.60);zone:SetInput('SoftEdge',0.20)
local exposure=node('BrightnessContrast','RetainTheEmptyPlace',2,0)
exposure.Input=plate.Output;exposure.EffectMask=zone.Mask
exposure:SetInput('Gain',0.65)
exposure.Blend:SetExpression('min(1,max(0,(time-2)/22))')
local function glyph(name,s,x,y,size,first,last)
 local t=node('TextPlus',name,2,y*8)
 t:SetInput('StyledText',s);t:SetInput('Font','Noto Serif CJK SC');t:SetInput('Style','Bold')
 t:SetInput('Size',size);t:SetInput('Center',{x,y});t:SetInput('Red1',0.78);t:SetInput('Green1',0.82);t:SetInput('Blue1',0.81)
 t.Alpha1:SetExpression('0.92*min(1,max(0,(time-'..first..')/'..(last-first)..'))')
 return t
end
local a=glyph('Shi','失',0.285,0.65,0.175,5,22)
local b=glyph('Zhen','帧',0.425,0.405,0.145,12,30)
local letters=node('Merge','StaggeredTitle',4,2);letters.Background=a.Output;letters.Foreground=b.Output
local grain=node('Merge','RainInsideLetters',6,2)
grain.Background=letters.Output;grain.Foreground=plate.Output;grain.EffectMask=letters.Output
grain:SetInput('Blend',0.28)
local title=node('Merge','TitleInEmptySpace',8,0)
title.Background=exposure.Output;title.Foreground=grain.Output
local pillar=node('RectangleMask','ActualVerticalMullion',6,4)
pillar:SetInput('Center',{0.3905,0.52});pillar:SetInput('Width',0.007);pillar:SetInput('Height',0.88);pillar:SetInput('SoftEdge',0.0005)
local occlusion=node('Merge','KeepExistingMullionInFront',10,0)
occlusion.Background=title.Output;occlusion.Foreground=plate.Output;occlusion.EffectMask=pillar.Mask
local out=assert(c:FindTool('MediaOut1'));out.Input=occlusion.Output
local saver=node('Saver','FusionRenderedFrames',12,0)
saver.Input=occlusion.Output;saver.Clip=root..'/fusion-render/title_0000.png'
saver:SetInput('OutputFormat','PNGFormat')
c:Unlock()
assert(pm:SaveProject(),'Project save failed')
assert(item:ExportFusionComp(root..'/title-trial.comp',1),'Export failed')
print('FUSION_SETUP_READY',p:GetName(),c:GetAttrs().COMPN_RenderEnd)
r:OpenPage('fusion')
local done=c:Render({Start=0,End=71,Wait=true,HiQ=true,Tool=saver})
print('FUSION_RENDER_DONE',tostring(done))
pm:SaveProject()
