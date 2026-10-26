local p=resolve:GetProjectManager():GetCurrentProject()
assert(p:GetName()=='Shizhen-B-Layered-20261027')
local c=p:GetCurrentTimeline():GetItemListInTrack('video',1)[1]:GetFusionCompByIndex(1)
print('B2_FULL_RENDER',c:Render({Start=0,End=71,Wait=true,HiQ=true,Tool=c:FindTool('BMotionFrames')}))
