# import os
# import maya.cmds as cmds

# CLASS_NAME = "ModuleA"
# TITLE = "Module A"
# DESCRIPTION = "Test description for module A"
# ICON = f"{os.environ['RIGGING_TOOL_ROOT']}/Icons/_hand.xpm"

# class ModuleA():
#     def __init__(self, user_specified_name) -> None:
#         self.module_name = CLASS_NAME
#         self.user_specified_name = user_specified_name
#         self.module_namespace = f"{self.module_name}__{self.user_specified_name}"
#         self.container_name = f"{self.module_namespace}:module_container"
#         self.joint_info = [["root_joint", [0.0, 0.0, 0.0]], ["end_joint", [4.0, 0.0, 0.0]]]
        
#     def install(self):
#         cmds.namespace(setNamespace=":")
#         cmds.namespace(add=self.module_namespace)
#         self.joints_grp = cmds.group(empty=True, name=f"{self.module_namespace}:joints_grp")
#         self.module_grp = cmds.group(self.joints_grp, name=f"{self.module_namespace}:module_grp")
        
#         cmds.container(self.container_name, addNode=self.module_grp, ihb=True) 
        
#         cmds.select(clear=True)
        
#         index = 0
#         joints = []
        
#         for joint in self.joint_info:
#             joint_name = joint[0]
#             joint_pos = joint[1]
            
#             if index > 0:
#                 parent_joint = f"{self.module_namespace}:{self.joint_info[index - 1][0]}"
#                 cmds.select(parent_joint, replace=True)
                
#             joint_name_full = cmds.joint(n=f"{self.module_namespace}:{joint_name}", p=joint_pos)
#             joints.append(joint_name_full)
            
#             index += 1


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
        self.container_name = f"{self.module_namespace}:module_container"
        self.joint_info = [["root_joint", [0.0, 0.0, 0.0]], ["end_joint", [4.0, 0.0, 0.0]]]
        
    def install(self):
        cmds.namespace(setNamespace=":")
        cmds.namespace(add=self.module_namespace)
        self.joints_grp = cmds.group(empty=True, name=f"{self.module_namespace}:joints_grp")
        self.module_grp = cmds.group(self.joints_grp, name=f"{self.module_namespace}:module_grp")
        
        if not cmds.objExists(self.container_name):
            cmds.container(name=self.container_name)
        cmds.container(self.container_name, edit=True, addNode=self.module_grp, ihb=True)
        
        cmds.select(clear=True)
        
        index = 0
        joints = []
        
        for joint in self.joint_info:
            joint_name = joint[0]
            joint_pos = joint[1]
            
            parent_joint = ""
            if index > 0:
                parent_joint = f"{self.module_namespace}:{self.joint_info[index - 1][0]}"
                cmds.select(parent_joint, replace=True)
                
            joint_name_full = cmds.joint(n=f"{self.module_namespace}:{joint_name}", p=joint_pos)
            joints.append(joint_name_full)
            
            
            cmds.container(self.container_name, edit=True, addNode=joint_name_full)
            cmds.container(self.container_name, edit=True, publishAndBind=[f"{joint_name_full}.rotate", f"{joint_name}_R"])
            cmds.container(self.container_name, edit=True, publishAndBind=[f"{joint_name_full}.rotateOrder", f"{joint_name}_rotateOrder"])
              
            if index > 0:
                cmds.joint(parent_joint, edit=True, orientJoint="xyz", sao="yup")
            
            index += 1
             
        cmds.parent(joints[0], self.joints_grp, absolute=True)
        cmds.lockNode(self.container_name, lock=True, lockUnpublished=True)

        # return joints  
