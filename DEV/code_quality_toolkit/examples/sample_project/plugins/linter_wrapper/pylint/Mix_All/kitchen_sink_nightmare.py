import sys, os  # L2: Multiple imports (C0410), Unused (W0611)
from datetime import * # L2: Wildcard (W0401)
import non_existent_module  # L3: Import error (E0401)

bad_global_var = 10  # L1: Invalid name (C0103)

# L1: Line too long (C0301)
# This comment is intentionally way too long to trigger the line length convention error in pylint which usually defaults to 100 chars.

class badClassName:  # L1: Invalid class name (C0103)
    def __init__(self):
        self.public = 1
        self._private = 2

    def NoSelfArgument():  # L3: Method has no argument (E0211)
        return "Fail"

def Bad_Function_Name(x, y=[]):  # L1: Naming (C0103), L2: Mutable default (W0102)
    global bad_global_var  # L2: Global statement (W0603)
    a = 1; b = 2  # L1: Multiple statements (C0321)
    unused_var = "z"  # L2: Unused (W0612)

    if x == True:  # L1: Singleton comparison (C0121)
        eval("print('Hazard')")  # L2: Eval (W0123)

    try:
        a.append(5)  # L3: No member (E1101)
    except:  # L2: Bare except (W0702)
        pass

    return x
    print("Unreachable")  # L2: Unreachable (W0101)

print(undefined_variable)  # L3: Undefined (E0602)
