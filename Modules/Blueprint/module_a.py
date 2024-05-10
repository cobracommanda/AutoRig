import os
import maya.cmds as cmds

CLASS_NAME = "ModuleA"
TITLE = "Module A"
DESCRIPTION = "Test description for module A"
ICON = f"{os.environ['RIGGING_TOOL_ROOT']}/Icons/_hand.xpm"

class ModuleA():
    def __init__(self, user_specified_name) -> None:
        self.module_name = CLASS_NAME
        self.user_specified_name = user_specified_name
        self.module_namespace = f"{self.module_name}__{self.user_specified_name}"
        
        
    def install(self):
        cmds.namespace(setNamespace=":")
        cmds.namespace(add=self.module_namespace)