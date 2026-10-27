local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local pm=resolve:GetProjectManager();local p=pm:GetCurrentProject();assert(p:GetName()=='Shizhen-B-Layered-20261027');local item=p:GetCurrentTimeline():GetItemListInTrack('video',1)[1];local c=item:GetFusionCompByIndex(1)
assert(not c:FindTool('SeparateShi'),'B5 already exists; inspect first')
local fit=c:FindTool('MatchPlateRaster')
local split='if(x<0.39,1,if(y>0.53,1,if(x<0.43,if(y>0.42,1,0),0)))'
local function separate(name,expression,x,y)
 local t=assert(c:AddTool('Custom',x,y));t:SetAttrs({TOOLS_Name=name});t.Image1=fit.Output;t:SetInput('Intermediate1',expression)
 t:SetInput('RedExpression','r1*i1');t:SetInput('GreenExpression','g1*i1');t:SetInput('BlueExpression','b1*i1');t:SetInput('AlphaExpression','a1*i1');return t
end
local shi=separate('SeparateShi',split,2,14)
local zhen=separate('SeparateZhen','1-('..split..')',2,17)
local function place(name,source,size,center,x,y)
 local t=assert(c:AddTool('Transform',x,y));t:SetAttrs({TOOLS_Name=name});t.Input=source.Output;t:SetInput('Size',size);t:SetInput('Center',center);return t
end
local a=place('ShiInLeftGlass',shi,0.50,{0.409,0.62},4,14)
local b=place('ZhenAcrossEmptyMullion',zhen,0.53,{0.458,0.51},4,17)
local group=assert(c:AddTool('Merge',6,15));group:SetAttrs({TOOLS_Name='PillarAsInterval'});group.Background=a.Output;group.Foreground=b.Output
c:FindTool('LatentSilverInk').Image1=group.Output
local clean=c:FindTool('GlyphOnlyArea');clean:SetInput('Center',{0.366,0.5});clean:SetInput('Width',0.34);clean:SetInput('Height',0.95)
local saver=c:FindTool('BMotionFrames');saver.Clip=root..'/render-B5/title_0000.png'
assert(item:ExportFusionComp(root..'/B5.comp',1));assert(pm:SaveProject())
for _,f in ipairs({72,96,120,143}) do print('B5_STILL',f,c:Render({Start=f,End=f,Wait=true,HiQ=true,Tool=saver})) end
print('B5_STILLS_DONE')
