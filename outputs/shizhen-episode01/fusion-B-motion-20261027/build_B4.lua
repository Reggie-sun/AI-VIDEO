local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
local pm=resolve:GetProjectManager();local p=pm:GetCurrentProject();assert(p:GetName()=='Shizhen-B-Layered-20261027');local item=p:GetCurrentTimeline():GetItemListInTrack('video',1)[1];local c=item:GetFusionCompByIndex(1)
assert(not c:FindTool('DistantDensityCarrier'),'B4 already exists: inspect first')
local plate=c:FindTool('OriginalMovingPlate')
local low=assert(c:AddTool('Blur',1,-2));low:SetAttrs({TOOLS_Name='DistantDensityCarrier'});low.Input=plate.Output;low:SetInput('XBlurSize',12);low:SetInput('YBlurSize',12)
local tone=c:FindTool('PhotographicDensity');tone.Image2=low.Output
-- Colour and broad urban density are separated from living rain/detail.
tone.NumberIn1:SetExpression('min(1,max(0,(time-14)/46))')
tone.NumberIn2:SetExpression('min(1,max(0,(time-30)/60))')
tone:SetInput('Intermediate1','0.2126*r1+0.7152*g1+0.0722*b1')
tone:SetInput('Intermediate2','0.2126*r2+0.7152*g2+0.0722*b2')
tone:SetInput('Intermediate3','0.93-0.68*i2')
tone:SetInput('Intermediate4','i1*i1*i1')
tone:SetInput('Intermediate5','i1-i2')
for _,v in ipairs({{'RedExpression','r1','r2',0.985},{'GreenExpression','g1','g2',0.993},{'BlueExpression','b1','b2',1}}) do
 tone:SetInput(v[1], '('..v[3]..'*(1-n1*0.78)+i2*n1*0.78)*(1-n2)+((i3*'..v[4]..')*(1-i4)+'..v[3]..'*i4)*n2+('..v[2]..'-'..v[3]..')*(1+0.12*n2)')
end
local ink=c:FindTool('LatentSilverInk');ink.Image3=low.Output
ink.NumberIn1:SetExpression('min(1,max(0,(time-46)/60))')
ink.NumberIn2:SetExpression('min(1,max(0,(time-88)/32))')
ink:SetInput('Intermediate1','0.2126*r2+0.7152*g2+0.0722*b2')
ink:SetInput('Intermediate2','0.2126*r3+0.7152*g3+0.0722*b3')
ink:SetInput('Intermediate3','min(1,max(0,(n1-(0.12+0.5*i2))*2.4))')
ink:SetInput('Intermediate4','min(1,abs(i1-i2)*10)')
ink:SetInput('Intermediate5','a1*(i3*(0.20+0.8*i4)*(1-n2)+n2)*(0.95-0.28*i1*i1*i1)')
for _,v in ipairs({{'RedExpression',0.018},{'GreenExpression',0.021},{'BlueExpression',0.023}}) do ink:SetInput(v[1],'('..v[2]..'+max(0,i1-i2)*0.32)*i5') end
ink:SetInput('AlphaExpression','i5')
local saver=c:FindTool('BMotionFrames');saver.Clip=root..'/render-B4/title_0000.png'
assert(item:ExportFusionComp(root..'/B4.comp',1));assert(pm:SaveProject())
for _,f in ipairs({0,48,72,96,120,143}) do print('B4_STILL',f,c:Render({Start=f,End=f,Wait=true,HiQ=true,Tool=saver})) end
print('B4_STILLS_DONE')
