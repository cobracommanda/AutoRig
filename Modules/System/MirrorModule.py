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
        self.module_names = []
        for module in self.modules:
            self.module_names.append(module.partition("__")[2])
        self.same_mirror_settings_for_all = False
        
        if len(self.modules) > 1:
            result = cmds.confirmDialog(title="Mirror Multilple Module", message=f"{str(len(self.modules))} modules selected for mirror.\nHow would you like to apply mirror settings?", b=["Same for all", "Individually", "Cancel"], db= "Same for all", cb="Cancel", ds="Cancel")
            
            if result == "Cancel":
                return
            elif result == "Same for all":
                self.same_mirror_settings_for_all = True
        
        self.UI_elements = {}
        
        if cmds.window("mirror_module_UI_window", exists=True):
            cmds.deleteUI("mirror_module_UI_window")
        
        window_width = 300
        window_height = 400
        scroll_width = window_width - 30

        mirror_plane_text_width = 80
        mirror_plane_radio_width = (scroll_width - mirror_plane_text_width) / 3

        self.UI_elements['window'] = cmds.window("mirror_module_UI_window", w=window_width, h=window_height, t="Mirror Module(s)", s=0)
        self.UI_elements['scroll_layout'] = cmds.scrollLayout(hst=0)
        self.UI_elements['top_column_layout'] = cmds.columnLayout(adj=1, rs=3)

        self.UI_elements['mirror_plane_row_column'] = cmds.rowColumnLayout(
            nc=4, 
            cat=[(1, "right", 0), (2, "both", 0), (3, "both", 0), (4, "both", 0)], 
            cw=[
                (1, mirror_plane_text_width), 
                (2, mirror_plane_radio_width), 
                (3, mirror_plane_radio_width), 
                (4, mirror_plane_radio_width)
            ]
        )

        cmds.text(l="Mirror Plane: ")
        self.UI_elements["mirror_plane_radio_collection"] = cmds.radioCollection()
        cmds.radioButton("XY", l="XY", sl=0)
        cmds.radioButton("YZ", l="YZ", sl=1)
        cmds.radioButton("XZ", l="XZ", sl=0)

        cmds.setParent(self.UI_elements['top_column_layout'])
        cmds.separator()
        cmds.text(l="Mirrored Name (s):")
        
        column_width = scroll_width / 2
        self.UI_elements['module_name_row_column'] = cmds.rowColumnLayout(nc=2, cat=(1, "right", 0) ,cw=[(1, column_width), (2, column_width)])
        for module in self.module_names:
            cmds.text(l=f"{module} >> ")
            self.UI_elements["moduleName_"+module] = cmds.textField(en=1, tx=f"{module}_mirror")
        
        
        cmds.showWindow(self.UI_elements['window'])
        
        
