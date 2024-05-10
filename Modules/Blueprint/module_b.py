import os

CLASS_NAME = "ModuleB"
TITLE = "Module B"
DESCRIPTION = "Test description for module B"
ICON = f"{os.environ['RIGGING_TOOL_ROOT']}/Icons/_hinge.xpm"

class ModuleB():
    def __init__(self) -> None:
        print("We're in the constructor")
        
    def install(self):
        print(f"INSTALL {CLASS_NAME}")