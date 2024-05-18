from PySide2 import QtCore, QtWidgets, QtGui
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import System.utils as utils
import importlib
from functools import partial


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class Blueprint_UI(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(Blueprint_UI, self).__init__(parent or maya_main_window())
        self.module_instance = None
        self.setWindowTitle("Nardt Industries")
        self.setObjectName("BlueprintUIDialog")
        self.setMinimumSize(400, 598)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # Ensure the widget is destroyed on close
        self.button_references = {}
        self.ungroup_button = None
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.job_num = None
        self.create_script_job()

    def showEvent(self, event):
        super().showEvent(event)
        self.create_script_job()  # Recreate the script job when the UI is shown

    def hideEvent(self, event):
        self.delete_script_job()  # Delete the script job when the UI is hidden
        super().hideEvent(event)

    def closeEvent(self, event):
        self.delete_script_job()  # Delete the script job when the UI is closed
        super().closeEvent(event)

    def create_script_job(self):
        if self.job_num is None:
            self.job_num = cmds.scriptJob(event=["SelectionChanged", self.modify_selected], parent=self.objectName())

    def delete_script_job(self):
        if self.job_num and cmds.scriptJob(exists=self.job_num):
            cmds.scriptJob(kill=self.job_num, force=True)
            self.job_num = None

    def modify_selected(self, *args):
        selected_nodes = cmds.ls(sl=1)
        control_enable = False  # Initialize control_enable at the beginning

        if len(selected_nodes) <= 1:
            self.module_instance = None
            selected_module_namespace = None
            current_module_file = None

            if len(selected_nodes) == 1:
                last_selected = selected_nodes[0]
                namespace_and_node = utils.strip_leading_namespace(last_selected)
                if namespace_and_node:
                    namespace = namespace_and_node[0]
                    module_name_info = utils.find_all_module_names("/Modules/Blueprint")
                    valid_modules = module_name_info[0]
                    valid_modules_names = module_name_info[1]

                    index = 0
                    for module_name in valid_modules_names:
                        module_name_inc_suffix = f"{module_name}__"
                        if namespace.find(module_name_inc_suffix) == 0:
                            current_module_file = valid_modules[index]
                            selected_module_namespace = namespace
                            break
                        index += 1

            user_specified_name = ""

            if selected_module_namespace:
                control_enable = True
                user_specified_name = selected_module_namespace.partition("__")[2]
                mod = __import__(f"Blueprint.{current_module_file}", {}, {}, [current_module_file])
                importlib.reload(mod)

                ModuleClass = getattr(mod, mod.CLASS_NAME)
                self.module_instance = ModuleClass(user_specified_name, None)
                self.module_name_edit_top.setText(user_specified_name)
                
                if self.module_instance.is_root_constrained():
                    self.button_references['Constrain Root > Hook'].setText('Unconstrain Root')
                else:
                    self.button_references['Constrain Root > Hook'].setText('Constrain Root > Hook')

                # Clear existing widgets
                self.clear_rotation_order_widgets()
                # Add module-specific controls
                self.create_module_specific_controls()
            else:
                self.module_name_edit_top.setText("")
                self.clear_rotation_order_widgets()
        else:
            # Enable control when multiple nodes are selected
            control_enable = True

        # Enable or disable buttons based on control_enable flag
        buttons_to_enable = ['Re-hook', 'Snap Root > Hook', 'Constrain Root > Hook', 'Group Selected', 'Mirror Module', 'Delete']
        for button_text in buttons_to_enable:
            if button_text in self.button_references:
                self.button_references[button_text].setEnabled(control_enable)
        # Ensure "Group Selected" is always enabled
        if 'Group Selected' in self.button_references:
            self.button_references['Group Selected'].setEnabled(True)

        # "Ungroup" button is handled separately
        if self.ungroup_button:
            self.ungroup_button.setEnabled(False)

    def create_module_specific_controls(self):
        # Clear existing controls
        while self.rotation_order_layout.count():
            child = self.rotation_order_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add new controls if module instance is available
        if self.module_instance:
            self.module_instance.UI(self, self.rotation_order_layout)

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
            'Re-hook', 'Snap Root > Hook', 'Constrain Root > Hook', 'Group Selected', 'Ungroup', 'Mirror Module', ' ', 'Delete', ''
        ])

        self.lock_button = QtWidgets.QPushButton("Lock")
        self.publish_button = QtWidgets.QPushButton("Publish")

        self.module_widgets = []
        for module in utils.find_all_modules("Modules/Blueprint"):
            module_data = self.dynamic_import(module)
            if module_data:
                self.module_widgets.append(self.create_module_widget(module_data, module))

        self.rotation_order_scroll_area = self.create_rotation_order_scroll_area()

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

    def add_rotation_order_widget(self, label_text, combo_items, joint):
        joint_label = QtWidgets.QLabel(label_text)
        rotation_order_combo = QtWidgets.QComboBox()
        rotation_order_combo.addItems(combo_items)

        try:
            # Attempt to get the current rotation order of the joint
            current_rotation_order = cmds.getAttr(f"{joint}.rotateOrder")
            rotation_order_combo.setCurrentIndex(current_rotation_order)

            # Connect the combo box change signal to update the joint's rotation order
            rotation_order_combo.currentIndexChanged.connect(partial(self.update_joint_rotation_order, joint))

            self.rotation_order_layout.addWidget(joint_label)
            self.rotation_order_layout.addWidget(rotation_order_combo)
        except ValueError as e:
            # Handle the error if the joint does not exist
            # print(f"joint locked removing {joint}.rotateOrder: {e} ui element")
            pass
            # Optionally, you can add a message or log the error



    def update_joint_rotation_order(self, joint, index):
        cmds.setAttr(f"{joint}.rotateOrder", index)

    def clear_rotation_order_widgets(self):
        while self.rotation_order_layout.count():
            child = self.rotation_order_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def create_rotation_order_scroll_area(self):
        self.rotation_scroll_area = QtWidgets.QScrollArea()
        self.rotation_scroll_area.setWidgetResizable(True)
        self.rotation_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.rotation_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.rotation_scroll_area_widget_contents = QtWidgets.QWidget()
        self.rotation_scroll_area.setWidget(self.rotation_scroll_area_widget_contents)

        self.rotation_order_layout = QtWidgets.QVBoxLayout(self.rotation_scroll_area_widget_contents)
        self.rotation_order_layout.setAlignment(QtCore.Qt.AlignTop)

        return self.rotation_scroll_area

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

        blueprint_layout.addWidget(self.rotation_order_scroll_area)

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
        
        hook_obj = self.find_hook_object_from_selection()
        
        
        try:
            module_path = f"Blueprint.{module}"
            mod = __import__(module_path, fromlist=[module])
            importlib.reload(mod)
            ModuleClass = getattr(mod, mod.CLASS_NAME)
            module_instance = ModuleClass(user_spec_name, hook_obj)
            module_instance.install()
            module_transform = f"{mod.CLASS_NAME}__{user_spec_name}:module_transform"
            cmds.select(module_transform, r=1)
            cmds.setToolTo("moveSuperContext")
        except Exception as e:
            self.display_error(f"An error occurred with {module}: {e}")

    def create_connections(self):
        self.lock_button.clicked.connect(self.question)
        self.module_name_edit_top.editingFinished.connect(self.rename_module)
        for button in self.buttons:
            if button.text() != '':
                button.clicked.connect(self.button_clicked)
                
    
    def lock(self, *args):
        module_info = []  # Store (module, user_specified_name) pairs
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
                module_inst = ModuleClass(module[1], None)
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

        for module in module_instances:
            module[0].lock_phase_2(module[1])
            
        for module in module_instances:
            hook_object = module[1][4]
            module[0].lock_phase_3(hook_object)

    def button_clicked(self):
        sender = self.sender()
        print(f"Button {sender.text()} clicked")  # For debugging
        if sender.text() == "Delete":
            self.delete_module()
        elif sender.text() == "Re-hook":
            self.rehook_module_setup()
        elif sender.text() == 'Snap Root > Hook':
            self.snap_root_to_hook()
        elif sender.text() == 'Constrain Root > Hook':
            self.constrain_root_to_hook()
            sender.setText('Unconstrain Root')  # Change the button label
        elif sender.text() == 'Unconstrain Root':
            self.unconstrain_root_to_hook()
            sender.setText('Constrain Root > Hook')  # Change the button label back
            

    def setup_buttons(self, button_texts):
        controls = []
        for index, text in enumerate(button_texts):
            if index == 8:  # If it's the ninth element
                checkbox = QtWidgets.QCheckBox("Symmetry Move")
                controls.append(checkbox)
            elif text == '':
                continue
            else:
                button = QtWidgets.QPushButton(text)
                if index != 3:  # Skip disabling the "Group Selected" button
                    button.setEnabled(False)  # Disable the button initially
                self.button_references[text] = button  # Store the button reference
                controls.append(button)
        return controls

    def delete_module(self, *args):
        self.module_instance.delete()
        cmds.select(cl=1)
        
    def rename_module(self):
        new_name = self.module_name_edit_top.text()
        self.module_instance.rename_module_instance(new_name)
        
        previous_selection = cmds.ls(sl=1)
        
        if len(previous_selection) > 0:
            cmds.select(previous_selection, r=1)
        else:
            cmds.select(cl=1)
            
    def find_hook_object_from_selection(self, *args):
        selected_objects = cmds.ls(sl=1, tr=1)
        
        number_of_objects = len(selected_objects)
        hook_obj = None
        
        if number_of_objects != 0:
            hook_obj = selected_objects[number_of_objects - 1]
        return hook_obj
    
    def rehook_module_setup(self, *args):
        selected_nodes = cmds.ls(sl=1, tr=1)
        if len(selected_nodes) == 2:
            new_hook = self.find_hook_object_from_selection()
            self.module_instance.rehook(new_hook)
        else:
            self.delete_script_job()
            current_selection = cmds.ls(sl=1)
            
            cmds.headsUpMessage("Please select the joint you wish to re-hook to. Clear selection to re-hook")
            cmds.scriptJob(event=["SelectionChanged", partial(self.rehook_module_callback, current_selection)], ro=1)
            
    def rehook_module_callback(self, current_selection):
        new_hook = self.find_hook_object_from_selection()
        self.module_instance.rehook(new_hook)
        if len(current_selection) > 0:
            cmds.select(current_selection, r=1)
        else:
            cmds.select(cl=1)
            
        self.create_script_job()
        
    def snap_root_to_hook(self, *args):
        self.module_instance.snap_root_to_hook()
        
    def constrain_root_to_hook(self, *args):
        self.module_instance.constrain_root_to_hook()
        
    def unconstrain_root_to_hook(self, *args):
        self.module_instance.unconstrain_root_to_hook()
            
