# 1. LINE_LENGTH: This specific line is intentionally written to be longer than the default 88 characters allowed by the configuration.

# 2. CLASS_NAMING: Class names should be CamelCase (e.g., BadStyleFile), not camelCase.
class badStyleFile:

    # 3. TRAILING_WHITESPACE: The line below has 4 extra spaces at the end.
    x = 1    

    # 4. FUNC_NAMING: Function names should be snake_case, not CamelCase.
    def BadFunctionName(self):
        
       # 5. INDENT_WIDTH: This line uses 3 spaces instead of the required 4.
       return True

# 6. INDENT_TABS_NOT_ALLOWED: The line below uses a hard Tab (\t) for indentation.
def tab_error():
	pass

# 7. INDENT_MIXED: The line below uses a Tab followed by a Space.
def mixed_error():
	 pass