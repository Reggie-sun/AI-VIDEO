local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local pm=resolve:GetProjectManager();local p=pm:GetCurrentProject();local item=p:GetCurrentTimeline():GetItemListInTrack('video',1)[1];local c=item:GetFusionCompByIndex(1)
local tone=c:FindTool('PhotographicDensity')
tone:SetInput('Intermediate2','min(1,max(0,(r1-b1)*7))*min(1,max(0,(i1-0.20)*5))')
tone:SetInput('Intermediate3','min(0.98,max(0.05,0.98-1.15*i1))')
tone:SetInput('Intermediate4','n2*0.96')
for i,v in ipairs({{0.188,0.5,0.033,1.12},{0.3905,0.5,0.009,1.12}}) do local t=c:FindTool('SourceProtection'..i);t:SetInput('Center',{v[1],v[2]});t:SetInput('Width',v[3]);t:SetInput('Height',v[4]);end
-- Badge remains present in the original photographic density, without a restored rectangular patch.
c:FindTool('KeepOriginalLayer3'):SetInput('Blend',0)
local saver=c:FindTool('BMotionFrames');saver.Clip=root..'/render-B2/title_0000.png'
assert(item:ExportFusionComp(root..'/B2.comp',1));assert(pm:SaveProject())
print('B2_STILL',c:Render({Start=60,End=60,Wait=true,HiQ=true,Tool=saver}))
