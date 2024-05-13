import os
import maya.cmds as cmds
import System.blueprint as blueprint_mod
import importlib

importlib.reload(blueprint_mod)

CLASS_NAME = "SingleJointSegment"
TITLE = "Single Joint Segment"
DESCRIPTION = "Creates 2 joints, with controls for it's joints orientation and rotate order. Ideal use: clavicle bone"
ICON = f"{os.environ['RIGGING_TOOL_ROOT']}/Icons/_singleJointSeg.xpm"



class SingleJointSegment(blueprint_mod.Blueprint):
    def __init__(self,user_specified_name) -> None:
        joint_info = [["root_joint", [0.0, 0.0, 0.0]], ["end_joint", [4.0, 0.0, 0.0]]]
        blueprint_mod.Blueprint.__init__(self, CLASS_NAME, user_specified_name, joint_info)
        
        
    def install_custom(self, joints):
        self.create_orientation_control(joints[0], joints[1])  