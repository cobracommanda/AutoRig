from PySide2 import QtCore, QtWidgets, QtGui
import maya.cmds as cmds
import System.utils as utils
import importlib
importlib.reload(utils)

class MirrorModule(QtWidgets.QDialog):
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
            
        temp_module_list = []
        for module in self.modules:
            if self.is_module_a_mirror(module):
                QtWidgets.QMessageBox.critical(self, "Error", "Cannot mirror a previously mirrored module, aborting mirror.")
                return
            
            if not self.can_module_be_mirrored(module):
                print(f"Module: {module} is of a module type that cannot be mirrored... skipping module. ")
            else:
                temp_module_list.append(module)
        self.modules = temp_module_list
        
        if len(self.modules) > 0:
            self.mirror_module_UI()
            
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
    
    def is_module_a_mirror(self, module):
        module_group = f"{module}:module_grp"
        return cmds.attributeQuery("mirrorLinks", n=module_group, ex=1)
    
    def can_module_be_mirrored(self, module):
        module_name_info = utils.find_all_module_names("/Modules/Blueprint")
        valid_modules = module_name_info[0]
        valid_module_names = module_name_info[1]
        
        module_name = module.partition("__")[0]
        
        if not module_name in valid_module_names:
             return False
        
        index = valid_module_names.index(module_name)
        mod = __import__(f"Blueprint.{valid_modules[index]}", {}, {}, valid_modules[index])
        importlib.reload(mod)
        
        ModuleClass = getattr(mod, mod.CLASS_NAME)
        module_inst = ModuleClass("null", None)
        
        return module_inst.can_module_be_mirrored()
    
    def mirror_module_UI(self):
        print(self.modules)