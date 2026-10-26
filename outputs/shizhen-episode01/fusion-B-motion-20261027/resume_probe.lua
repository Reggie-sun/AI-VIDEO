local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local p=assert(resolve:GetProjectManager():GetCurrentProject());assert(p:GetName()=='Shizhen-B-Layered-20261027')
local item=assert(p:GetCurrentTimeline():GetItemListInTrack('video',1)[1]);local c=assert(item:GetFusionCompByIndex(1))
local t=assert(c:AddTool('Custom',0,0));t:SetAttrs({TOOLS_Name='ProbeCustom'})
local resize=assert(c:AddTool('BetterResize',2,0));resize:SetAttrs({TOOLS_Name='ProbeResize'})
for _,tool in ipairs({t,resize}) do
 print(tool:GetAttrs().TOOLS_Name)
 for _,inp in pairs(tool:GetInputList()) do local a=inp:GetAttrs();if tostring(a.INPS_ID):find('Expression') or tostring(a.INPS_ID):find('Intermediate') or tostring(a.INPS_ID):find('Width') or tostring(a.INPS_ID):find('Height') then print(a.INPS_ID,a.INPS_Name) end end
end
resolve:GetProjectManager():SaveProject();item:ExportFusionComp(root..'/probe.comp',1);print('B_PROBE_READY')
