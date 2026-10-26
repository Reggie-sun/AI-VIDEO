local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-title-trial-20261026'
local r=assert(resolve);local pm=r:GetProjectManager();local p=assert(pm:GetCurrentProject())
assert(p:GetName()=='Shizhen-Fusion-Title-Trial-20261026')
local item=assert(p:GetCurrentTimeline():GetItemListInTrack('video',1)[1])
local c=assert(item:GetFusionCompByIndex(1))
-- Use premultiplied compositing blend, not shading alpha with surviving RGB.
c:FindTool('Shi').Alpha1:SetExpression('1')
c:FindTool('Zhen').Alpha1:SetExpression('1')
c:FindTool('TitleInEmptySpace').Blend:SetExpression('min(1,max(0,(time-5)/17))')
c:FindTool('StaggeredTitle').Blend:SetExpression('min(1,max(0,(time-12)/18))')
local saver=assert(c:FindTool('FusionRenderedFrames'))
saver.Clip=root..'/fusion-render-F2/title_0000.png'
assert(item:ExportFusionComp(root..'/title-trial-F2.comp',1))
assert(pm:SaveProject())
print('FUSION_F2_RENDER',c:Render({Start=0,End=71,Wait=true,HiQ=true,Tool=saver}))
