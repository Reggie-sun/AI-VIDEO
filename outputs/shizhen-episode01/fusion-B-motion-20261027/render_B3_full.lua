local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local pm=resolve:GetProjectManager();local p=pm:GetCurrentProject();assert(p:GetName()=='Shizhen-B-Layered-20261027');local item=p:GetCurrentTimeline():GetItemListInTrack('video',1)[1];local c=item:GetFusionCompByIndex(1)
-- Correct the inspected mask spill: the woman's entire body remains outside the density field.
local region=c:FindTool('EmptySpaceDensityRegion');region:SetInput('Center',{0.17,0.60});region:SetInput('Width',0.65);region:SetInput('SoftEdge',0.04)
assert(item:ExportFusionComp(root..'/B3-final.comp',1));assert(pm:SaveProject())
print('B3_FULL_RENDER',c:Render({Start=0,End=143,Wait=true,HiQ=true,Tool=c:FindTool('BMotionFrames')}))
