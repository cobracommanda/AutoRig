import os
import maya.cmds as cmds
import System.utils as utils


class Blueprint():
    def __init__(self,module_name, user_specified_name, joint_info) -> None:
        self.module_name = module_name
        self.user_specified_name = user_specified_name
        self.module_namespace = f"{self.module_name}__{self.user_specified_name}"
        self.container_name = f"{self.module_namespace}:module_container"
        self.joint_info = joint_info
        
    # Methods intended for overriding by derived class
    def install_custom(self, joints):
        print("install_custom() method is not implemented by derived class")
        
        
    
    #  Baseclass Methods   
    def install(self):
        cmds.namespace(setNamespace=":")
        cmds.namespace(add=self.module_namespace)
        self.joints_grp = cmds.group(empty=True, name=f"{self.module_namespace}:joints_grp")
        self.hierarchy_representation_grp = cmds.group(em=1, n=f"{self.module_namespace}:hierarchy_representation_grp")
        
        self.orientation_controls_grp = cmds.group(em=1, n=f"{self.module_namespace}:orientationControls_grp")
        self.module_grp = cmds.group([self.joints_grp, self.hierarchy_representation_grp, self.hierarchy_representation_grp], name=f"{self.module_namespace}:module_grp")
        
        if not cmds.objExists(self.container_name):
            cmds.container(name=self.container_name)
        utils.add_node_to_container(self.container_name, self.module_grp, ihb=1)
        
        
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
            
            cmds.setAttr(f"{joint_name_full}.visibility", 0)
            utils.add_node_to_container(self.container_name, joint_name_full)
            
            cmds.container(self.container_name, edit=True, publishAndBind=[f"{joint_name_full}.rotate", f"{joint_name}_R"])
            cmds.container(self.container_name, edit=True, publishAndBind=[f"{joint_name_full}.rotateOrder", f"{joint_name}_rotateOrder"])
              
            if index > 0:
                cmds.joint(parent_joint, edit=True, orientJoint="xyz", sao="yup")
            
            index += 1
             
        cmds.parent(joints[0], self.joints_grp, absolute=True)
        
        self.initialize_module_transform(self.joint_info[0][1])
        
        translations_controls = []
        for joint in joints:
            translations_controls.append(self.create_translation_controller_at_joints(joint))
            
        root_joint_point_constraint = cmds.pointConstraint(translations_controls[0], joints[0], mo=0, n=f"{joints[0]}_pointConstraint")
        utils.add_node_to_container(self.container_name, root_joint_point_constraint)
        
        
        # Setup stretchy joint segments
        for index in range(len(joints) - 1):
            self.setup_stretchy_joint_segment(joints[index], joints[index+1])
            
        self.install_custom(joints)
            
    
        utils.force_scene_update()
        cmds.lockNode(self.container_name, lock=True, lockUnpublished=True)
        
        

    def create_translation_controller_at_joints(self, joint):
        pos_control_file =  f"{os.environ['RIGGING_TOOL_ROOT']}/ControlObjects/Blueprint/translation_control.ma"
        cmds.file(pos_control_file, i=True)
        
        container = cmds.rename("translation_control_container", f"{joint}_translation_control_container")
        
        utils.add_node_to_container(self.container_name, container)
        
        for node in cmds.container(container, q=True, nodeList=True):
            cmds.rename(node, f"{joint}_{node}", ignoreShape=True)
             
        control = f"{joint}_translation_control"
        
        cmds.parent(control, self.module_transform, a=1)
        
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
        
        utils.add_node_to_container(self.container_name,[pole_vector_locator_grp, parent_constraint, child_point_constraint], ihb=1)
        
        for node in [ik_handle, root_locator, end_locator]:
            cmds.parent(node, self.joints_grp, a=1)
            cmds.setAttr(f"{node}.visibility", 0)
        
        self.create_hierarchy_representation(parent_joint, child_joint)
            
    def create_hierarchy_representation(self, parent_joint, child_joint):
        nodes = self.create_stretchy_object("/ControlObjects/Blueprint/hierarchy_representation.ma", "hierarchy_representation_container", 
                                            "hierarchy_representation", parent_joint, child_joint)
        
        constrained_grp = nodes[2] 
        cmds.parent(constrained_grp, self.hierarchy_representation_grp, r=1)
        
        
        
    
    def create_stretchy_object(self, object_relative_filepath, object_container_name, object_name, parent_joint, child_joint):
        object_file = f"{os.environ['RIGGING_TOOL_ROOT']}{object_relative_filepath}"
        cmds.file(object_file, i=1)
        object_container = cmds.rename(object_container_name, f"{parent_joint}_{object_container_name}")
        
        for node in cmds.container(object_container, q=1, nl=1):
            cmds.rename(node, f"{parent_joint}_{node}", ignoreShape=1)
            
        object = f"{parent_joint}_{object_name}"
        
        constrained_grp = cmds.group(em=1, n=f"{object}_parentConstraint_grp")
        cmds.parent(object, constrained_grp, a=1)
        
        parent_constraint = cmds.parentConstraint(parent_joint, constrained_grp, mo=0)[0]
        
        cmds.connectAttr(f"{child_joint}.translateX", f"{constrained_grp}.scaleX" )
        
        scale_constraint = cmds.scaleConstraint(self.module_transform, constrained_grp, sk="x", mo=0)[0]
        
        utils.add_node_to_container(object_container, [constrained_grp, parent_constraint, scale_constraint], ihb=1)
        utils.add_node_to_container(self.container_name, object_container)
        
        return (object_container, object, constrained_grp)
    
    
    def initialize_module_transform(self, root_pos):
        control_grp_file = f"{os.environ['RIGGING_TOOL_ROOT']}/ControlObjects/Blueprint/controlGroup_control.ma"
        cmds.file(control_grp_file, i=1)
        
        self.module_transform = cmds.rename("controlGroup_control", f"{self.module_namespace}:module_transform")
        cmds.xform(self.module_transform, ws=1, a=1, t=root_pos)
        
        utils.add_node_to_container(self.container_name, self.module_transform, ihb=1)
         
        # Setup global scaling
        cmds.connectAttr(f"{self.module_transform}.scaleY", f"{self.module_transform}.scaleX")
        cmds.connectAttr(f"{self.module_transform}.scaleY", f"{self.module_transform}.scaleZ")
        
        cmds.aliasAttr("globalScale", f"{self.module_transform}.scaleY")
        
        cmds.container(self.container_name, e=1, pb=[f"{self.module_transform}.translate", "moduleTransform_T"])
        cmds.container(self.container_name, e=1, pb=[f"{self.module_transform}.rotate", "moduleTransform_R"])
        cmds.container(self.container_name, e=1, pb=[f"{self.module_transform}.globalScale", "moduleTransform_globalScale"])
        
    def delete_hierarchy_representation(self, parent_joint):
        hierarchy_container =  f"{parent_joint}_hierarchy_representation_container"
        cmds.delete(hierarchy_container)
    
    
    def create_orientation_control(self, parent_joint, child_joint):
        self.delete_hierarchy_representation(parent_joint)
        
        nodes = self.create_stretchy_object("/ControlObjects/Blueprint/orientation_control.ma", "orientation_control_container", "orientation_control", parent_joint, child_joint)
        orientation_container = nodes[0]
        orientation_control = nodes[1]
        constrained_grp = nodes[2]
        
        cmds.parent(constrained_grp, self.orientation_controls_grp, r=1)
        parent_joint_without_namespace = utils.strip_all_namespaces(parent_joint)[1]
        attr_name = f"{parent_joint_without_namespace}_orientation"
        
        cmds.container(orientation_container, e=1, pb=[f"{orientation_control}.rotateX", attr_name])
        cmds.container(self.container_name, e=1, pb=[f"{orientation_container}.{attr_name}", attr_name])
        
        return orientation_control