# Save this file as: all_violations.py

# 1. LINE_LENGTH: This line should be well over 88 characters to test the maximum line length check in the 'analyze' method.

def func_with_trailing_whitespace():
    # 2. TRAILING_WHITESPACE: The line below ends with two spaces.  
    return True 

def another_func():
    # 3. INDENT_MIXED: The line below uses a mix of tab and spaces.
	 def nested_func():
	  pass # This line should have mixed indentation if manually edited

# 4. INDENT_TABS_NOT_ALLOWED: The line below uses only a tab character.
	if 1 == 1:
        pass

# 5. INDENT_WIDTH: The line below uses 5 spaces (not a multiple of 4).
     if 2 == 2:
        pass

# 6. CLASS_NAMING: The class name is lowercase, violating CamelCase.
class bad_class_name:
    
    # 7. FUNC_NAMING: The function name is CamelCase, violating snake_case.
    def BadFuncName(self):
        pass