from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
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
        # self.create_connections()

    def create_widgets(self):
        self.tab_widget = QtWidgets.QTabWidget()
        self.blueprint_tab = QtWidgets.QWidget()
        self.animation_tab = QtWidgets.QWidget()

    def create_layout(self):
        blueprint_layout = QtWidgets.QVBoxLayout(self.blueprint_tab)
        blueprint_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QtWidgets.QScrollArea(self.blueprint_tab)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        self.scroll_area_widget_contents = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget_contents)
        
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_area_widget_contents)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
        
        
        for module in utils.find_all_modules("Modules/Blueprint"):
            module_data = self.dynamic_import(module)
            item_widget = QtWidgets.QWidget()
            item_layout = QtWidgets.QHBoxLayout(item_widget)
            item_layout.setSpacing(0)
            item_widget.setFixedSize(380, 60)  # Adjust size as needed

            self.current_button = QtWidgets.QPushButton()
            icon = QtGui.QIcon(module_data[2])
            self.current_button.setIcon(icon)
            self.current_button.setIconSize(QtCore.QSize(40, 40))
            self.current_button.setFixedSize(50, 50)
            self.current_button.clicked.connect(partial(self.install_module, module))

            text_container = QtWidgets.QWidget()
            text_layout = QtWidgets.QVBoxLayout(text_container)
            text_layout.setSpacing(0)
            text_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to align closely with the button

            title_label = QtWidgets.QLabel(module_data[0])
            title_label.setAlignment(QtCore.Qt.AlignCenter)

            text_area = QtWidgets.QTextEdit(module_data[1])
            text_area.setFixedHeight(40)  # Adjust height to accommodate the title

            # Set padding at the bottom of the text area
            text_area.setStyleSheet("QTextEdit { padding-bottom: 10px; }")
            
            text_area.setReadOnly(True)

            text_layout.addWidget(title_label)
            text_layout.addWidget(text_area)

            item_layout.addWidget(self.current_button)
            item_layout.addWidget(text_container)

            self.scroll_layout.addWidget(item_widget)



        blueprint_layout.addWidget(self.scroll_area)
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

            # Access module attributes
            title = getattr(mod, 'TITLE', 'Default Title')
            description = getattr(mod, 'DESCRIPTION', 'No description provided.')
            icon_path = getattr(mod, 'ICON', '')

        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")
        except AttributeError as e:
            print(f"Error accessing attributes in {module_name}: {e}")
        except Exception as e:
            print(f"An error occurred with {module_name}: {e}")

        return (title, description, icon_path)
    
    
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
            
            
        except ImportError as e:
            print(f"Failed to import {module}: {e}")
        except AttributeError as e:
            print(f"Error accessing attributes in {mod.CLASS_NAME}: {e}")
        except Exception as e:
            print(f"An error occurred with {module}: {e}")
        
    def create_connections(self):
        self.current_button.clicked.connect(self.install_module)
