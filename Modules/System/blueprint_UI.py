from PySide2 import QtCore, QtGui, QtWidgets
from shiboken2 import wrapInstance

import sys
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import importlib
import System.utils as utils
from functools import partial

importlib.reload(utils)

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class Blueprint_UI(QtWidgets.QDialog):

    dlg_instance = None

    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = Blueprint_UI()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=None):
        if parent is None:
            parent = maya_main_window()
        super().__init__(parent)
        self.setWindowTitle("Nardt Industries")
        self.setMinimumSize(400, 598)
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.tab_widget = QtWidgets.QTabWidget()
        self.blueprint_tab = QtWidgets.QWidget()
        self.animation_tab = QtWidgets.QWidget()

        self.scroll_area = QtWidgets.QScrollArea(self.blueprint_tab)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area_widget_contents = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget_contents)

        self.module_name_edit_top = QtWidgets.QLineEdit()

        self.buttons = self.setup_buttons([
            'Rehook', 'Snap root to hook', 'Constraint root to hook', 
            'Group', 'Ungroup', 'Mirror', '', 'Delete', ''
        ])

        self.lock_button = QtWidgets.QPushButton("Lock")
        self.publish_button = QtWidgets.QPushButton("Publish")

        self.module_widgets = []
        for module in utils.find_all_modules("Modules/Blueprint"):
            module_data = self.dynamic_import(module)
            if module_data:
                self.module_widgets.append(self.create_module_widget(module_data, module))

    def create_module_widget(self, module_data, module):
        item_widget = QtWidgets.QWidget()
        item_layout = QtWidgets.QHBoxLayout(item_widget)
        item_layout.setSpacing(0)
        item_widget.setFixedSize(380, 60)

        button = QtWidgets.QPushButton()
        icon = QtGui.QIcon(module_data[2])
        button.setIcon(icon)
        button.setIconSize(QtCore.QSize(40, 40))
        button.setFixedSize(50, 50)
        button.clicked.connect(partial(self.install_module, module))

        text_container = QtWidgets.QWidget()
        text_layout = QtWidgets.QVBoxLayout(text_container)
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QtWidgets.QLabel(module_data[0])
        title_label.setAlignment(QtCore.Qt.AlignCenter)

        text_area = QtWidgets.QTextEdit(module_data[1])
        text_area.setFixedHeight(40)
        text_area.setStyleSheet("QTextEdit { padding-bottom: 10px; }")
        text_area.setReadOnly(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(text_area)

        item_layout.addWidget(button)
        item_layout.addWidget(text_container)

        return item_widget

    def create_layout(self):
        blueprint_layout = QtWidgets.QVBoxLayout(self.blueprint_tab)
        blueprint_layout.setContentsMargins(0, 0, 0, 0)
        blueprint_layout.addWidget(self.scroll_area)

        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_area_widget_contents)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)

        for widget in self.module_widgets:
            self.scroll_layout.addWidget(widget)

        form_layout_top = QtWidgets.QFormLayout()
        form_layout_top.addRow("Module Name:", self.module_name_edit_top)
        blueprint_layout.addLayout(form_layout_top)

        grid_layout = QtWidgets.QGridLayout()
        for i, button in enumerate(self.buttons):
            grid_layout.addWidget(button, i // 3, i % 3)
        blueprint_layout.addLayout(grid_layout)

        vbox_layout = QtWidgets.QVBoxLayout()
        vbox_layout.addWidget(self.lock_button)
        vbox_layout.addWidget(self.publish_button)
        blueprint_layout.addLayout(vbox_layout)

        blueprint_layout.addStretch(1)

        animation_layout = QtWidgets.QVBoxLayout(self.animation_tab)
        self.animation_tab.setLayout(animation_layout)

        self.tab_widget.addTab(self.blueprint_tab, "Blueprint")
        self.tab_widget.addTab(self.animation_tab, "Animation")

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def dynamic_import(self, module_name):
        try:
            module_path = f"Blueprint.{module_name}"
            mod = __import__(module_path, fromlist=[module_name])
            importlib.reload(mod)

            title = getattr(mod, 'TITLE', 'Default Title')
            description = getattr(mod, 'DESCRIPTION', 'No description provided.')
            icon_path = getattr(mod, 'ICON', '')

            return (title, description, icon_path)
        except Exception as e:
            self.display_error(f"Failed to import {module_name}: {e}")
            return None

    def display_error(self, message):
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText("Error: " + message)
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.exec_()
        
    def question(self):
        button_pressed = QtWidgets.QMessageBox.question(self, "Question", "Converting blueprints to joints is irreversible..\nOnce done, modifications will no longer be possible.\nDo you wish to proceed?")
        if button_pressed == QtWidgets.QMessageBox.Yes:
           self.lock()
        else:
            return
            
            
    def install_module(self, module, *args):
        basename = "instance_"
        cmds.namespace(setNamespace=":")
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True)
        for i in range(len(namespaces)):
            if namespaces[i].find("__") != -1:
                namespaces[i] = namespaces[i].partition("__")[2]
        new_suffix = utils.find_highest_trailing_number(namespaces, basename) + 1
        user_spec_name = f"{basename}{str(new_suffix)}"
        try:
            module_path = f"Blueprint.{module}"
            mod = __import__(module_path, fromlist=[module])
            importlib.reload(mod)
            ModuleClass = getattr(mod, mod.CLASS_NAME)
            module_instance = ModuleClass(user_spec_name)
            module_instance.install()
            module_transform = f"{mod.CLASS_NAME}__{user_spec_name}:module_transform"
            cmds.select(module_transform, r=1)
            cmds.setToolTo("moveSuperContext")
        except Exception as e:
            self.display_error(f"An error occurred with {module}: {e}")


    def create_connections(self):
        self.lock_button.clicked.connect(self.question)
        # self.publish_button = QtWidgets.QPushButton("Publish")
        for button in self.buttons:
            if button.text() != '':
                # Connect only functional buttons, ignore placeholders
                button.clicked.connect(self.button_clicked)
                
                
    def lock(self, *args):
        module_info = [] # Store (module, user_specified_name) pairs
        cmds.namespace(set=":")
        namespaces = cmds.namespaceInfo(ls=1)
        
        module_name_info = utils.find_all_module_names("/Modules/Blueprint")
        valid_modules = module_name_info[0]
        valid_module_names = module_name_info[1]
        
        for n in namespaces:
            split_string = n.partition("__")
            
            if split_string[1] != "":
                module = split_string[0]
                user_specified_name = split_string[2]
                
                if module in valid_module_names:
                    index = valid_module_names.index(module)
                    module_info.append([valid_module_names[index], user_specified_name])
                    
        if len(module_info) == 0:
            self.display_error("There appears to be no blueprint modules\ninstances in the current scene.\nAborting lock")
            return
        
        module_instances = []
        for module in module_info:
            module_name = "Blueprint." + module[0]
            try:
                mod = __import__(module_name, fromlist=[module[0]])
                importlib.reload(mod)
                
                ModuleClass = getattr(mod, mod.CLASS_NAME)
                module_inst = ModuleClass(user_specified_name=module[1])
                module_info = module_inst.lock_phase_1()
                
                module_instances.append((module_inst, module_info))
                
            except ModuleNotFoundError as e:
                print(f"ModuleNotFoundError: {e}")
                self.display_error(f"Module {module_name} not found.\nAborting lock")
                return
            except Exception as e:
                print(f"An error occurred: {e}")
                self.display_error(f"An error occurred while locking module {module_name}.\nAborting lock")
                return
        

    def button_clicked(self):
        sender = self.sender()
        print(f"Button {sender.text()} clicked")  # For debugging
        # Dispatch based on text
        # if sender.text() == "Rehook":
        #     self.handle_rehook()
        # elif sender.text() == "Delete":
        #     self.handle_delete()

    def setup_buttons(self, button_texts):
        controls = []
        for index, text in enumerate(button_texts):
            if index == 8:  # If it's the ninth element
                checkbox = QtWidgets.QCheckBox("Symmetry Move")
                controls.append(checkbox)
            elif text == '':
                # Ignore this since it's likely meant to be the placeholder you're replacing
                continue
            else:
                button = QtWidgets.QPushButton(text)
                controls.append(button)
        return controls
