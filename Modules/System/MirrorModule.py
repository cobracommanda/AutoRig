
import maya.cmds as cmds
import System.utils as utils
import importlib
importlib.reload(utils)

class MirrorModule:
    def __init__(self) -> None:
        selection = cmds.ls(sl=1, tr=1)
        if len(selection) == 0:
            return
        
        first_selected = selection[0]
        
        self.modules = []
        self.group = None
        if first_selected.find("Group__") == 0:
            self.modules = self.find_sub_modules(first_selected)
        else:
            module_namespace_info = utils.strip_leading_namespace(first_selected)
            self.modules.append(module_namespace_info[0])
            
        print(self.group)
        print(self.modules)
            
            
    def find_sub_modules(self, group):
        return_modules = []
        
        children = cmds.listRelatives(group, c=1)
        children = cmds.ls(children, tr=1)
        
        for child in children:
            if child.find("Group__") == 0:
                return_modules.extend(self.find_sub_modules(child))
            else:
                namespace_info = utils.strip_leading_namespace(child)
                if namespace_info != None and namespace_info[1] == "module_transform":
                    module = namespace_info[0]
                    return_modules.append(module)
                    
        return return_modules