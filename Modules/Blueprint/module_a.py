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
            
        root_joint_point_constraint = cmds.pointConstraint(translations_controls[0], joints[0], mo=0, n=f"{joints[0]}_pointConstraint")
        cmds.container(self.container_name, e=1, an=root_joint_point_constraint)
        
        
        # Setup stretchy joint segments
        for index in range(len(joints) - 1):
            self.setup_stretchy_joint_segment(joints[index], joints[index+1])
        
        utils.force_scene_update()
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
        
    def setup_stretchy_joint_segment(self, parent_joint, child_joint): 
        parent_translation_control = self.get_translation_control(parent_joint)
        child_translation_control = self.get_translation_control(child_joint)
        
        
        pole_vector_locator = cmds.spaceLocator(n=f"{parent_translation_control}_poleVectorLocator")[0]
        pole_vector_locator_grp = cmds.group(n=f"{pole_vector_locator}_parentConstraintGrp")
        
        cmds.parent(pole_vector_locator_grp, self.module_grp, a=1)
        parent_constraint = cmds.parentConstraint(parent_translation_control, pole_vector_locator_grp, mo=0)[0]
        cmds.setAttr(f"{pole_vector_locator}.visibility", 0)
        cmds.setAttr(f"{pole_vector_locator}.ty", -0.5)
        
        ik_nodes = utils.basic_stretchy_IK(parent_joint, child_joint, container=self.container_name, lockMinimumLength=False,
                                           poleVectorObject=pole_vector_locator, scaleCorrectionAttribute=None)
        
        ik_handle = ik_nodes['ik_handle']
        root_locator = ik_nodes['root_locator']
        end_locator = ik_nodes['end_locator']
        # root_locator_point_constraint = ik_nodes['root_locator_point_constraint']
        # ik_handle_point_constraint = ik_nodes['ik_handle_point_constraint']
        # ik_effector  = ik_nodes['ik_effector']
        # root_locator = ik_nodes['root_locator']
        # poleVectorObject = ik_nodes['poleVectorObject']
        
        child_point_constraint = cmds.pointConstraint(child_translation_control, end_locator, mo=0, n=f"{end_locator}_pointConstraint")[0]
        
        cmds.container(self.container_name, e=1, an=[pole_vector_locator_grp, parent_constraint, child_point_constraint], ihb=1) 
        for node in [ik_handle, root_locator, end_locator]:
            cmds.parent(node, self.joints_grp, a=1)
            cmds.setAttr(f"{node}.visiblilty", 0)
        
