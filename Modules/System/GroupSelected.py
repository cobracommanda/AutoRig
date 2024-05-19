# import os
# import maya.cmds as cmds
# from functools import partial
# import System.utils as utils
# import importlib

# importlib.reload(utils)

# class GroupSelected:
#     def __init__(self) -> None:
#         self.objects_to_group = []
        
#     def show_UI(self): 
#         self.find_selection_to_group()
#         print(self.objects_to_group)
        
#     def find_selection_to_group(self):
#         selected_objects = cmds.ls(sl=1, tr=1)
        
#         self.objects_to_group = []
#         for obj in selected_objects:
#             valid = False
            
#             if obj.find("module_transform") != -1:
#                 split_string = obj.rsplit("module_transform")
#                 if split_string[1] == "":
#                     valid = True
                    
#             if valid == False and obj.find("Group__") == 0:
#                 valid = True
                
#             if valid == True:
#                 self.objects_to_group.append(obj)
                
                
                
from PySide2 import QtCore, QtWidgets, QtGui
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import System.utils as utils
import importlib
from functools import partial

importlib.reload(utils)

def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class GroupUI(QtWidgets.QDialog):
    dlg_instance = None  # Class-level instance variable

    def __init__(self, parent=maya_main_window()):
        super(GroupUI, self).__init__(parent)

        self.setWindowTitle("Group Selected")
        self.setMinimumWidth(200)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = GroupUI()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def create_widgets(self):
        self.lineedit = QtWidgets.QLineEdit()
        self.ok_btn = QtWidgets.QPushButton("Accept")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        
        self.position_radiobutton1 = QtWidgets.QRadioButton("Last Selected")
        self.position_radiobutton2 = QtWidgets.QRadioButton("Average Position")
        
        self.position_radiobutton1.setChecked(True)

        # Group radio buttons to ensure only one can be selected at a time
        self.position_radiobutton_group = QtWidgets.QButtonGroup()
        self.position_radiobutton_group.addButton(self.position_radiobutton1)
        self.position_radiobutton_group.addButton(self.position_radiobutton2)

    def create_layouts(self):
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Group Name:", self.lineedit)
        
        position_layout = QtWidgets.QHBoxLayout()
        position_layout.addWidget(self.position_radiobutton1)
        position_layout.addWidget(self.position_radiobutton2)
        form_layout.addRow("Positioned at:", position_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.cancel_btn.clicked.connect(self.close)
        self.ok_btn.clicked.connect(self.on_ok_btn_clicked)
        self.lineedit.editingFinished.connect(self.on_editing_finished)
        self.position_radiobutton1.toggled.connect(self.on_position_radiobutton1_toggled)
        self.position_radiobutton2.toggled.connect(self.on_position_radiobutton2_toggled)

    def on_editing_finished(self):
        print(f"Group Name: {self.lineedit.text()}")

    def on_position_radiobutton1_toggled(self, checked):
        if checked:
            print("Positioned at: Last Selected")

    def on_position_radiobutton2_toggled(self, checked):
        if checked:
            print("Positioned at: Average Position")
            
    def on_ok_btn_clicked(self):
        group_name = self.lineedit.text()
        position = "Last Selected" if self.position_radiobutton1.isChecked() else "Average Position"
        print(f"Group Name: {group_name}")
        print(f"Positioned at: {position}")


class GroupSelected:
    def __init__(self) -> None:
        self.objects_to_group = []

    def show_UI(self):
        self.find_selection_to_group()
        print(self.objects_to_group)

        # Show the dialog
        GroupUI.show_dialog()

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

    def group_select(self, *args):
        import System.GroupSelected as group_selected
        importlib.reload(group_selected)

        group_selected.GroupSelected().show_UI()


if __name__ == "__main__":
    try:
        test_dialog.close()  # pylint: disable=E0601
        test_dialog.deleteLater()
    except:
        pass

    test_dialog = GroupUI()
    test_dialog.show()
