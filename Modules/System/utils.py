import maya.cmds as cmds

def find_all_modules(relative_directory):
    all_py_files = find_all_files(relative_directory, ".py")
    
    return_modules = []
    for the_file in all_py_files:
        if the_file != "__init__":
            return_modules.append(the_file)
            
    return return_modules
    
    
def find_all_files(relative_directory, file_extension):
    import os
    file_directory = f"{os.environ['RIGGING_TOOL_ROOT']}/{relative_directory}/"
    all_files = os.listdir(file_directory)
    
    return_files = []
    
    for current_file in all_files:
        split_string = str(current_file).rpartition(file_extension)
        
        if not split_string[1] == "" and split_string[2] =="":
            return_files.append(split_string[0])
            
            
    return return_files


def find_highest_trailing_number(names, basename):
    import re 
    
    highest_value = 0
    
    for n in names:
        if n.find(basename) == 0:
            suffix = n.partition(basename)[2]
            if re.match("^[0-9]*$", suffix):
                numerical_element = int(suffix)

                if numerical_element > highest_value:
                    highest_value = numerical_element
            
    return highest_value
        
        
def strip_leading_namespace(nodename):
    if str(nodename).find(":") == -1:
        return None
    split_string = str(nodename).partition(":")
    return [split_string[0], split_string[2]]
    
    
def strip_all_namespaces(nodename):
    if str(nodename).find(":") == -1:
        return None
        
    split_string = str(nodename).rpartition(":")
    return [split_string[0], split_string[2]]
    
    
def basic_stretchy_IK(root_joint, end_joint, container=None, lockMinimumLength=True, poleVectorObject=None, scaleCorrectionAttribute=None):
    from math import fabs
    contained_nodes = []
    
    total_original_length = 0.0
    done = False
    parent = root_joint
    child_joints = []
    
    while not done:
        children = cmds.listRelatives(parent, children=True)
        children = cmds.ls(children, type="joint")
        
        if len(children) == 0:
            done = True
        else:
            child = children[0]
            child_joints.append(child)
            total_original_length += fabs(cmds.getAttr(f"{child}.translateX"))
            parent = child
            
            if child == end_joint:
                done = True
                 
    
    # Create RP IK on joint chain
    ik_nodes = cmds.ikHandle(sj=root_joint, ee=end_joint, sol="ikRPsolver", n=f"{root_joint}_ikHandle")
    ik_nodes[1] = cmds.rename(ik_nodes[1], f"{root_joint}_ikEffector")
    ik_effector = ik_nodes[1]
    ik_handle = ik_nodes[0]
    
    cmds.setAttr(f"{ik_handle}.visibility", 0)
    contained_nodes.extend(ik_nodes) 
    
    # Create pole vector locator
    if poleVectorObject == None:
        poleVectorObject = cmds.spaceLocator(n=f"{ik_handle}_poleVectorLocator")[0]
        contained_nodes.append(poleVectorObject)
        
        cmds.xform(poleVectorObject, ws=True, a=True, t=cmds.xform(root_joint, q=True, ws=True, t=True))
        cmds.xform(poleVectorObject, ws=True, r=True, t=[0.0, 1.0, 0.0])
        cmds.setAttr(f"{poleVectorObject}.visibility", 0)
        
    pole_vector_constraint = cmds.poleVectorConstraint(poleVectorObject, ik_handle)[0]
    contained_nodes.append(pole_vector_constraint)
    
    # Create root and end locators
    root_locator = cmds.spaceLocator(n=f"{root_joint}_rootPosLocator")[0]
    root_locator_point_constraint = cmds.pointConstraint(root_joint, root_locator, mo=0, n=f"{root_locator}_pointConstraint")[0]
    end_locator = cmds.spaceLocator(n=f"{end_joint}_endPosLocator")[0]
    cmds.xform(end_locator, ws=1, a=1, t=cmds.xform(ik_handle, q=1, ws=1, t=1))
    ik_handle_point_constraint = cmds.pointConstraint(end_locator, ik_handle, mo=0, n=f"{ik_handle}_pointConstraint")[0]
    
    contained_nodes.extend([root_locator, end_locator, root_locator_point_constraint, ik_handle_point_constraint])
    cmds.setAttr(f"{root_locator}.visibility", 0)
    cmds.setAttr(f"{end_locator}.visibility", 0)
    
    
    # Grab distance between locators
    root_locator_without_namespace = strip_all_namespaces(root_locator)[1]
    end_locator_without_namespace = strip_all_namespaces(end_locator)[1]
    
    module_namespace = strip_all_namespaces(root_joint)[0]
    
    dist_node = cmds.shadingNode("distanceBetween", au=1, n=f"{module_namespace}:distBetween_{root_locator_without_namespace}_{end_locator_without_namespace}")
    contained_nodes.append(dist_node)
    
    cmds.connectAttr(f"{root_locator}Shape.worldPosition[0]", f"{dist_node}.point1")
    cmds.connectAttr(f"{end_locator}Shape.worldPosition[0]", f"{dist_node}.point2")
    
    scale_attr = f"{dist_node}.distance"
    
    # Divide distance by total original length = scale factor
    scale_factor = cmds.shadingNode("multiplyDivide", au=1, n=f"{ik_handle}_scaleFactor")
    contained_nodes.append(scale_factor)
    
    cmds.setAttr(f"{scale_factor}.operation", 2) # Divide
    cmds.connectAttr(scale_attr, f"{scale_factor}.input1X")
    cmds.setAttr(f"{scale_factor}.input2X", total_original_length)
    
    translation_driver = f"{scale_factor}.outputX"
    
    # Connect joints to stretchy calculations
    for joint in child_joints:
        mult_node = cmds.shadingNode("multiplyDivide", au=1, n=f"{joint}_scaleMultiply")
        contained_nodes.append(mult_node)
        
        cmds.setAttr(f"{mult_node}.input1X", cmds.getAttr(f"{joint}.translateX"))
        cmds.connectAttr(translation_driver, f"{mult_node}.input2X")
        cmds.connectAttr(f"{mult_node}.outputX", f"{joint}.translateX")
    
    
    if container != None:
        add_node_to_container(container, contained_nodes, ihb=1)
        
        
    return_dict = {}
    return_dict['ik_handle'] = ik_handle
    return_dict['ik_handle_point_constraint'] = ik_handle_point_constraint
    return_dict['ik_effector'] = ik_effector 
    return_dict['root_locator'] = root_locator
    return_dict['root_locator_point_constraint'] = root_locator_point_constraint
    return_dict['end_locator'] = end_locator
    return_dict['poleVectorObject'] = poleVectorObject
    
    return return_dict


def force_scene_update():
    cmds.setToolTo("moveSuperContext")
    nodes = cmds.ls()
    
    for node in nodes:
        cmds.select(node, r=1)
        
    cmds.select(cl=1)
    
    cmds.setToolTo("selectSuperContext")
    
def add_node_to_container(container, nodes_in, ihb=False, include_shapes=False, force=False):
    nodes = []
    if isinstance(nodes_in, list):
        nodes = list(nodes_in)
    else:
        nodes = [nodes_in]

        
    conversion_nodes = []    
    for node in nodes:
        node_conversion_nodes = cmds.listConnections(node, source=True, destination=True)
        node_conversion_nodes = cmds.ls(node_conversion_nodes, type="unitConversion")
        
        conversion_nodes.extend(node_conversion_nodes)
        
    nodes.extend(conversion_nodes)
    cmds.container(container, edit=True, addNode=nodes, ihb=ihb, includeShapes=include_shapes, force=force)