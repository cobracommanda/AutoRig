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
        
    def lock_phase_1(self):
        """
        Gather and return all required information from this module's control objects
        joint_positions = a list of joint positions, from root down the hierarchy
        joint_orientations = a list of orientations, or a list of axis information (orient_joint and secondary_axis_orient for joint command)
                                # These are passed in the following tuple: (orientations, None) or (None, axis_info)
        joint_rotation_orders = a list of joint rotation orders (integer values gathered with getAttr)
        joint_preferred_angles = a list of joint preferred angles, optional (can pass None)
        hook_object = self.find_hook_object_for_lock()
        root_transform = a bool, either True or False. True = R,T, and S on root joint. False = R only
        module_info = (joint_positions, joint_orientations, joint_rotation_orders, joint_preferred_angles, hook_object)
        return module_info
        """
        return None
        
    
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
    
    
    def get_joints(self):
        joint_basename = f"{self.module_namespace}:"
        joints = []
        
        for joint_inf in self.joint_info:
            joints.append(f"{joint_basename}{joint_inf[0]}")
            
        return joints
    
    def get_orientation_control(self, joint_name):
        return f"{joint_name}_orientation_control"
    
    def orientation_controlled_joint_get_orientation(self, joint, clean_parent):
        new_clean_parent = cmds.duplicate(joint, po=1)[0]
        
        if not clean_parent in cmds.listRelatives(new_clean_parent, p=1):
            cmds.parent(new_clean_parent, clean_parent, a=1)
            
        cmds.makeIdentity(new_clean_parent, a=1, r=1, s=0, t=0)
        orientation_control = self.get_orientation_control(joint)
        
        cmds.setAttr(f"{new_clean_parent}.rotateX", cmds.getAttr(f"{orientation_control}.rotateX"))
        
        cmds.makeIdentity(new_clean_parent, a=1, r=1, s=0, t=0)
        
        orientX =  cmds.getAttr(f"{new_clean_parent}.jointOrientX")
        orientY =  cmds.getAttr(f"{new_clean_parent}.jointOrientY")
        orientZ =  cmds.getAttr(f"{new_clean_parent}.jointOrientZ")
        
        orientation_values = (orientX, orientY, orientZ)
        
        return (orientation_values, new_clean_parent)
    
    def lock_phase_2(self, module_info):
        joint_positions = module_info[0]
        num_joints = len(joint_positions)
        joint_orientations = module_info[1]
        orient_with_axis = False
        pure_orientations = False
        
        if joint_orientations[0] == None:
            orient_with_axis = True
            joint_orientations = joint_orientations[1]
        else:
            pure_orientation = True
            joint_orientations = joint_orientations[0]
            
        num_orientations = len(joint_orientations)
        joint_rotation_orders = module_info[2] 
        num_rotation_orders = len(joint_rotation_orders)
        joint_preferred_angles = module_info[3]
        num_preferred_angles = 0
        
        if joint_preferred_angles != None:
            num_preferred_angles = len(joint_preferred_angles)
            
        hook_object = module_info[4]
        root_transform = module_info[5]
        
        # Delete our blueprint controls
        cmds.lockNode(self.container_name, l=0, lu=0)
        cmds.delete(self.container_name)
        cmds.namespace(set=":")
        
        joint_radius = 1
        if num_joints == 1:
            joint_radius = 1.5
            
        new_joints = []
        for i in range(num_joints):
            new_joint = ""
            cmds.select(cl=1)
            
            if orient_with_axis:
                new_joint = cmds.joint(n=f"{self.module_namespace}:blueprint_{self.joint_info[i][0]}",
                                        p=joint_positions[i], roo="xyz", rad=joint_radius)
                
                if i != 0:
                    cmds.parent(new_joint, new_joints[i-1], a=1)
                    offset_index = i - 1
                    
                    if offset_index < num_orientations:
                        cmds.joint(new_joints[offset_index], e=1, oj=joint_orientations[offset_index][0], sao=joint_orientations[offset_index][1])
                        cmds.makeIdentity(new_joint, r=1, a=1)
                    
            else:
                if i != 0:
                    cmds.select(new_joints[i-1])
                    joint_orientation  = [0.0, 0.0, 0.0]
                    
                if i < num_orientations:
                    joint_orientation = [joint_orientations[i][0], joint_orientations[i][1], joint_orientations[i][2]]
                    
                new_joint = cmds.joint(n=f"{self.module_namespace}:blueprint_{self.joint_info[i][0]}",
                                        p=joint_positions[i], o=joint_orientation, roo="xyz", rad=joint_radius)
                
            new_joints.append(new_joint)
            
            if i < num_rotation_orders:
                cmds.setAttr(f"{new_joint}.rotateOrder", int(joint_rotation_orders[i]))
                
            if i < num_preferred_angles:
                cmds.setAttr(f"{new_joint}.preferredAngleX", joint_preferred_angles[i][0])
                cmds.setAttr(f"{new_joint}.preferredAngleY", joint_preferred_angles[i][1])
                cmds.setAttr(f"{new_joint}.preferredAngleZ", joint_preferred_angles[i][2])
                cmds.setAttr(f"{new_joint}.segmentScaleCompensate", 0)
                
        blueprint_grp = cmds.group(em=1, n=f"{self.module_namespace}:blueprint_joint_grp")
        cmds.parent(new_joints[0], blueprint_grp, a=1)
        
        creation_pose_grp_nodes = cmds.duplicate(blueprint_grp, n=f"{self.module_namespace}:creation_pose_joint_grp", rc=1)
        creation_pose_grp = creation_pose_grp_nodes[0]
        
        creation_pose_grp_nodes.pop(0)
        
        i = 0
        for node in creation_pose_grp_nodes:
            renamed_node = cmds.rename(node, f"{self.module_namespace}:creation_pose_{self.joint_info[i][0]}")
            cmds.setAttr(f"{renamed_node}.visibility", 0)
            i += 1
    
        cmds.select(blueprint_grp, r=1)
        cmds.addAttr(at="bool", dv=0, ln="controlModulesInstalled", k=0)
        setting_locator = cmds.spaceLocator(n=f"{self.module_namespace}:SETTINGS")[0]
        cmds.setAttr(f"{setting_locator}.visibility", 0)
        
        cmds.select(setting_locator, r=1)
        cmds.addAttr(at="enum", ln="activeModule", en="None:", k=0)
        cmds.addAttr(at="float", ln="creationPoseWeight", dv=1, k=0)