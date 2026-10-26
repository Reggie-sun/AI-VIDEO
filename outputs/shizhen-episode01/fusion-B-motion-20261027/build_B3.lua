local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local pm=resolve:GetProjectManager();local p=pm:GetCurrentProject();assert(p:GetName()=='Shizhen-B-Layered-20261027');local item=p:GetCurrentTimeline():GetItemListInTrack('video',1)[1];local c=item:GetFusionCompByIndex(1)
c:SetAttrs({COMPN_GlobalStart=0,COMPN_GlobalEnd=143,COMPN_RenderStart=0,COMPN_RenderEnd=143})
local plate=c:FindTool('OriginalMovingPlate');plate.Clip=root..'/source-retime/plate_0001.png';plate:SetAttrs({TOOLNT_Clip_Start={0},TOOLNT_Clip_End={143}})
local tone=c:FindTool('PhotographicDensity')
tone.NumberIn1:SetExpression('min(1,max(0,(time-10)/40))')
tone.NumberIn2:SetExpression('min(1,max(0,(time-32)/58))')
tone:SetInput('Intermediate2','i1*i1*i1')
tone:SetInput('Intermediate3','0.96-0.65*sqrt(max(0,i1))')
tone:SetInput('Intermediate4','n2')
for _,v in ipairs({{'RedExpression','r1',0.985},{'GreenExpression','g1',0.993},{'BlueExpression','b1',1.0}}) do tone:SetInput(v[1],'('..v[2]..'*(1-n1)+i1*n1)*(1-i4)+(i3*'..v[3]..'*(1-i2)+'..v[2]..'*i2)*i4') end
local region=assert(c:AddTool('EllipseMask',1,4));region:SetAttrs({TOOLS_Name='EmptySpaceDensityRegion'});region:SetInput('Center',{0.19,0.60});region:SetInput('Width',0.86);region:SetInput('Height',1.40);region:SetInput('SoftEdge',0.12)
c:FindTool('DevelopEmptySpace').EffectMask=region.Mask
local place=c:FindTool('FixedTitlePlacement');place:SetInput('Size',0.56);place:SetInput('Center',{0.26,0.55})
local ink=c:FindTool('LatentSilverInk');ink.NumberIn1:SetExpression('min(1,max(0,(time-54)/54))')
ink:SetInput('Intermediate2','min(1,max(0,(n1-(0.08+0.40*i1))*3))')
local ground=assert(c:AddTool('RectangleMask',13,9));ground:SetAttrs({TOOLS_Name='KeepGroundDepth'});ground:SetInput('Center',{0.5,0.075});ground:SetInput('Width',1.1);ground:SetInput('Height',0.28);ground:SetInput('SoftEdge',0.055)
local merge=assert(c:AddTool('Merge',14,1));merge:SetAttrs({TOOLS_Name='PreserveWetGround'});merge.Background=c:FindTool('KeepOriginalLayer3').Output;merge.Foreground=plate.Output;merge.EffectMask=ground.Mask
c:FindTool('MediaOut1').Input=merge.Output
local saver=c:FindTool('BMotionFrames');saver.Input=merge.Output;saver.Clip=root..'/render-B3/title_0000.png'
assert(item:ExportFusionComp(root..'/B3.comp',1));assert(pm:SaveProject())
for _,f in ipairs({0,48,84,120,143}) do print('B3_STILL',f,c:Render({Start=f,End=f,Wait=true,HiQ=true,Tool=saver})) end
print('B3_STILLS_DONE')
