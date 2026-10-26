local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local r=assert(resolve);local pm=r:GetProjectManager()
assert(not pm:LoadProject('Shizhen-B-Layered-20261027'),'Existing B attempt: inspect instead of recreate')
local p=assert(pm:CreateProject('Shizhen-B-Layered-20261027'))
p:SetSetting('timelineFrameRate','24');p:SetSetting('timelineResolutionWidth','1920');p:SetSetting('timelineResolutionHeight','1080')
local tl=assert(p:GetMediaPool():CreateEmptyTimeline('B-Layered-72'));p:SetCurrentTimeline(tl);r:OpenPage('edit')
local item=assert(tl:InsertFusionCompositionIntoTimeline());local c=assert(item:GetFusionCompByIndex(1))
c:SetAttrs({COMPN_GlobalStart=0,COMPN_GlobalEnd=71,COMPN_RenderStart=0,COMPN_RenderEnd=71})
c:SetPrefs({['Comp.FrameFormat.Width']=1920,['Comp.FrameFormat.Height']=1080,['Comp.FrameFormat.Rate']=24})
local t=assert(c:AddTool('Custom',0,0));t:SetAttrs({TOOLS_Name='ProbeCustom'})
local resize=assert(c:AddTool('Resize',2,0));resize:SetAttrs({TOOLS_Name='ProbeResize'})
local f=assert(io.open(root..'/fusion-inputs.txt','w'))
for _,tool in ipairs({t,resize}) do
 f:write(tool:GetAttrs().TOOLS_Name..'\n')
 for _,inp in pairs(tool:GetInputList()) do local a=inp:GetAttrs();f:write(tostring(a.INPS_ID)..' | '..tostring(a.INPS_Name)..' | '..tostring(a.INPS_DataType)..'\n') end
end
f:close();pm:SaveProject();item:ExportFusionComp(root..'/probe.comp',1);r:OpenPage('fusion');print('B_PROBE_READY')
