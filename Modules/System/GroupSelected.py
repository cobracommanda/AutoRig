import os
from PySide2 import QtCore, QtWidgets, QtGui
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import System.utils as utils
import importlib
from functools import partial
import maya.utils  # Import maya.utils for executeDeferred

importlib.reload(utils)

def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class GroupUI(QtWidgets.QDialog):
    dlg_instance = None  # Class-level instance variable

    def __init__(self, group_selected_instance, parent=maya_main_window()):
        super(GroupUI, self).__init__(parent)
        self.group_selected_instance = group_selected_instance

        self.setWindowTitle("Group Selected")
        self.setMinimumWidth(200)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    @classmethod
    def show_dialog(cls, group_selected_instance):
        if not cls.dlg_instance:
            cls.dlg_instance = GroupUI(group_selected_instance)

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def create_widgets(self):
        self.lineedit = QtWidgets.QLineEdit()
        self.ok_btn = QtWidgets.QPushButton("Accept")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        
        self.position_last_selected_btn = QtWidgets.QPushButton("Position at Last Selected")
        self.position_average_position_btn = QtWidgets.QPushButton("Position at Average Position")

        # Default to "Last Selected" option
        self.position_last_selected_btn.setCheckable(True)
        self.position_last_selected_btn.setChecked(True)
        self.position_average_position_btn.setCheckable(True)

        # Group buttons to ensure only one can be selected at a time
        self.position_button_group = QtWidgets.QButtonGroup()
        self.position_button_group.addButton(self.position_last_selected_btn)
        self.position_button_group.addButton(self.position_average_position_btn)

    def create_layouts(self):
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Group Name:", self.lineedit)

        position_layout = QtWidgets.QHBoxLayout()
        position_layout.addWidget(self.position_last_selected_btn)
        position_layout.addWidget(self.position_average_position_btn)
        form_layout.addRow(position_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.cancel_btn.clicked.connect(self.cancel_option)
        self.ok_btn.clicked.connect(self.accepted_option)
        self.lineedit.editingFinished.connect(self.on_editing_finished)

    def on_editing_finished(self):
        print(f"Group Name: {self.lineedit.text()}")

    def position_last_selected(self):
        if not self.group_selected_instance.objects_to_group:
            QtWidgets.QMessageBox.warning(self, "Warning", "No objects selected for grouping.")
            return

        self.group_selected_instance.create_temporary_group_representation()
        self.group_selected_instance.create_at_last_selected()
        cmds.select(self.group_selected_instance.temp_group_transform)
        maya.utils.executeDeferred(self.set_move_tool)

    def position_average_position(self):
        if not self.group_selected_instance.objects_to_group:
            QtWidgets.QMessageBox.warning(self, "Warning", "No objects selected for grouping.")
            return

        self.group_selected_instance.create_temporary_group_representation()
        self.group_selected_instance.create_at_average_position()
        cmds.select(self.group_selected_instance.temp_group_transform)
        maya.utils.executeDeferred(self.set_move_tool)

    def accepted_option(self):
        group_name = self.lineedit.text()
        # position = "Last Selected" if self.position_last_selected_btn.isChecked() else "Average Position"
        # print(f"Group Name: {group_name}")
        # print(f"Positioned at: {position}")
        
         
        if self.position_last_selected_btn.isChecked():
            self.position_last_selected()
        elif self.position_average_position_btn.isChecked():
            self.position_average_position()
        if self.create_group(group_name) != None:
            self.accept()

    def cancel_option(self):
        if self.group_selected_instance.temp_group_transform and cmds.objExists(self.group_selected_instance.temp_group_transform):
            cmds.delete(self.group_selected_instance.temp_group_transform)
        self.close()

    def set_move_tool(self):
        print("Setting move tool...")
        cmds.setToolTo("moveSuperContext")
        print("Move tool set.")
        
    def create_group(self, group_name):
        group_name = self.lineedit.text()
        full_group_name = f"Group__{group_name}"
        if cmds.objExists(full_group_name):
            QtWidgets.QMessageBox.warning(None, "Name Conflict\nWarning", f"Group \\{group_name}\\ already exists")
            return None
        group_transform = cmds.rename(self.group_selected_instance.temp_group_transform, full_group_name)
        
        group_container = "Group_container"
        if not cmds.objExists(group_container):
            cmds.container(n=group_container)
            
        containers = [group_container]
        
        for obj in self.group_selected_instance.objects_to_group:
            if obj.find("Group__") == 0:
                continue
            obj_namespace = utils.strip_leading_namespace(obj)[0]
            containers.append(f"{obj_namespace}:module_container")
        
        for c in containers:
            cmds.lockNode(c, l=0, lu=0)
        
        if len(self.group_selected_instance.objects_to_group) != 0:
            temp_group = cmds.group(self.group_selected_instance.objects_to_group, a=1)
            group_parent = cmds.listRelatives(temp_group, p=1)
            
            if group_parent != None:
                cmds.parent(group_transform, group_parent[0], a=1)
                
            cmds.parent(self.group_selected_instance.objects_to_group, group_transform, a=1)
            cmds.delete(temp_group)

        self.add_group_to_container(group_transform)
        
        for c in containers:
            cmds.lockNode(c, l=1, lu=1)
            
        cmds.setToolTo("moveSuperContext")
        cmds.select(group_transform, r=1)
        
        return group_transform
        
    def add_group_to_container(self, group):
        group_container = "Group_container"
        utils.add_node_to_container(group_container, group, include_shapes=True)
        group_name = group.partition("Group__")[2]
        
        # Ensure valid attribute alias names
        if group_name[0].isdigit():
            group_name = "_" + group_name
            
        cmds.container(group_container, e=1, pb=[f"{group}.translate", f"{group_name}_t"])
        cmds.container(group_container, e=1, pb=[f"{group}.rotate", f"{group_name}_r"])
        cmds.container(group_container, e=1, pb=[f"{group}.globalScale", f"{group_name}_globalScale"])
        


class GroupSelected:
    def __init__(self) -> None:
        self.objects_to_group = []
        self.temp_group_transform = None  # Initialize to None

    def show_UI(self):
        self.find_selection_to_group()
        if not self.objects_to_group:
            QtWidgets.QMessageBox.warning(None, "Warning", "No objects selected for grouping.")
            return

        print(self.objects_to_group)
        GroupUI.show_dialog(self)

    def find_selection_to_group(self):
        selected_objects = cmds.ls(sl=1, tr=1)

        self.objects_to_group = []
        for obj in selected_objects:
            valid = False

            if obj.find("module_transform") != -1:
                split_string = obj.rsplit("module_transform")
                if split_string[1] == "":
                    valid = True

            if not valid and obj.find("Group__") == 0:
                valid = True

            if valid:
                self.objects_to_group.append(obj)

    def create_temporary_group_representation(self):
        control_grp_file = f"{os.environ['RIGGING_TOOL_ROOT']}/ControlObjects/Blueprint/controlGroup_control.ma"
        cmds.file(control_grp_file, i=1)
        
        self.temp_group_transform = cmds.rename("controlGroup_control", "Group__tempGroupTransform")
        
        cmds.connectAttr(f"{self.temp_group_transform}.scaleY", f"{self.temp_group_transform}.scaleX") 
        cmds.connectAttr(f"{self.temp_group_transform}.scaleY", f"{self.temp_group_transform}.scaleZ")
        
        for attr in ['scaleX', 'scaleZ', 'visibility']:
            cmds.setAttr(f"{self.temp_group_transform}.{attr}", l=1, k=0)
            
        cmds.aliasAttr("globalScale", f"{self.temp_group_transform}.scaleY")

    def create_at_last_selected(self, *args):
        if self.objects_to_group:
            control_pos = cmds.xform(self.objects_to_group[-1], q=1, ws=1, t=1)
            cmds.xform(self.temp_group_transform, ws=1, a=1, t=control_pos)
            print(f"Moved {self.temp_group_transform} to {control_pos}")
        else:
            QtWidgets.QMessageBox.warning(None, "Warning", "No objects selected to determine position.")

    def create_at_average_position(self, *args):
        if self.objects_to_group:
            control_pos = [0.0, 0.0, 0.0]
            for obj in self.objects_to_group:
                obj_pos = cmds.xform(obj, q=1, ws=1, t=1)
                control_pos[0] += obj_pos[0]
                control_pos[1] += obj_pos[1]
                control_pos[2] += obj_pos[2]
            
            number_of_objects = len(self.objects_to_group)
            if number_of_objects:
                control_pos[0] /= number_of_objects  
                control_pos[1] /= number_of_objects  
                control_pos[2] /= number_of_objects
        
                cmds.xform(self.temp_group_transform, ws=1, a=1, t=control_pos) 
                print(f"Moved {self.temp_group_transform} to {control_pos}")
            else:
                QtWidgets.QMessageBox.warning(None, "Warning", "No objects selected to determine average position.")
        else:
            QtWidgets.QMessageBox.warning(None, "Warning", "No objects selected to determine position.")

    def group_select(self, *args):
        import System.GroupSelected as group_selected
        importlib.reload(group_selected)

        group_selected.GroupSelected().show_UI()


if __name__ == "__main__":
    try:
        group_dialog.close()  # pylint: disable=E0601
        group_dialog.deleteLater()
    except:
        pass

    group_dialog = GroupUI(None)
    group_dialog.show()


class UngroupSelected:
    def __init__(self) -> None:
        selected_objects = cmds.ls(sl=1, tr=1)

        filtered_groups = [obj for obj in selected_objects if obj.startswith("Group__")]

        if not filtered_groups:
            return

        group_container = "Group_container"
        modules = []

        for group in filtered_groups:
            modules.extend(self.find_child_modules(group))

        module_containers = [group_container]
        for module in modules:
            module_containers.append(f"{module}:module_container")

        for container in module_containers:
            cmds.lockNode(container, l=0, lu=0)

        self.process_groups(filtered_groups)

        for container in module_containers:
            cmds.lockNode(container, l=1, lu=1)

        self.cleanup_empty_group_container(group_container)

    def find_child_modules(self, group):
        modules = []
        children = cmds.listRelatives(group, c=1)

        if children:
            for child in children:
                module_namespace_info = utils.strip_leading_namespace(child)
                if module_namespace_info:
                    modules.append(module_namespace_info[0])
                elif child.startswith("Group__"):
                    modules.extend(self.find_child_modules(child))

        return modules

    def process_groups(self, groups):
        parent_groups = set()

        for group in groups:
            parent = cmds.listRelatives(group, parent=True)
            if parent:
                parent_groups.add(parent[0])

            children = cmds.listRelatives(group, c=1)
            if children and len(children) > 1:
                cmds.ungroup(group, a=1)

            for attr in ['t', 'r', 'globalScale']:
                cmds.container("Group_container", e=1, ubp=f"{group}.{attr}")

            cmds.delete(group)

        self.cleanup_empty_groups(parent_groups)

    def cleanup_empty_groups(self, parent_groups):
        for parent in parent_groups:
            children = cmds.listRelatives(parent, c=1)
            if not children:
                cmds.delete(parent)

    def cleanup_empty_group_container(self, group_container):
        container_content = cmds.container(group_container, q=True, nodeList=True)
        if not container_content:
            cmds.lockNode(group_container, l=0, lu=0)
            cmds.delete(group_container)
        else:
            non_empty_nodes = [node for node in container_content if cmds.listRelatives(node, c=1)]
            if not non_empty_nodes:
                cmds.lockNode(group_container, l=0, lu=0)
                cmds.delete(group_container)

if __name__ == "__main__":
    UngroupSelected()
