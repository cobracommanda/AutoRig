import os

CLASS_NAME = "ModuleA"
TITLE = "Module A"
DESCRIPTION = "Test description for module A"
ICON = f"{os.environ['RIGGING_TOOL_ROOT']}/Icons/_hand.xpm"

class ModuleA():
    def __init__(self) -> None:
        print("We're in the constructor")
        
    def install(self):
        print(f"INSTALL {CLASS_NAME}")