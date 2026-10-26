local root='/home/reggie/vscode_folder/AI-VIDEO/outputs/shizhen-episode01/fusion-B-motion-20261027'
for k,v in pairs(resolve:Fusion():GetRegList()) do
 local a=v:GetAttrs();local id=tostring(a.REGS_ID);local n=tostring(a.REGS_Name)
 if id:lower():find('custom') or id:lower():find('resize') or n:lower():find('custom') or n:lower():find('resize') then
 print(id,n)
 end
end
print('REGISTRY_INSPECTED')
