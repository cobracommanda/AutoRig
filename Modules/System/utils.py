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
    
    
def basic_stretchy_IK(root_joint, end_joint, container=None, lockMinimumLength=True, poleVectorObject=None, scaleCorrectionAttribute=None):
    contained_nodes = []
    
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