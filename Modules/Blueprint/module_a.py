import os
import maya.cmds as cmds
import System.utils as utils

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
        
        translations_controls = []
        for joint in joints:
            translations_controls.append(self.create_translation_controller_at_joints(joint))
        
        cmds.lockNode(self.container_name, lock=True, lockUnpublished=True)

    def create_translation_controller_at_joints(self, joint):
        pos_control_file =  f"{os.environ['RIGGING_TOOL_ROOT']}/ControlObjects/Blueprint/translation_control.ma"
        cmds.file(pos_control_file, i=True)
        
        container = cmds.rename("translation_control_container", f"{joint}_translation_control_container")
        cmds.container(self.container_name, edit=True, addNode=container)
        
        for node in cmds.container(container, q=True, nodeList=True):
            cmds.rename(node, f"{joint}_{node}", ignoreShape=True)
             
        control = f"{joint}_translation_control"
        
        joint_pos = cmds.xform(joint, q=True, worldSpace=True, translation=True)
        cmds.xform(control, worldSpace=True, absolute=True, translation=joint_pos)
        
        nice_name = utils.strip_leading_namespace(joint)[1]
        
        attr_name = f"{nice_name}_T"
        
        cmds.container(container, edit=True, publishAndBind=[f"{control}.translate", attr_name])
        cmds.container(self.container_name, edit=True, publishAndBind=[f"{container}.{attr_name}", attr_name])
        
        return control
    
    def get_translation_control(self, joint_name):
        return f"{joint_name}_translation_control"
        