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
    