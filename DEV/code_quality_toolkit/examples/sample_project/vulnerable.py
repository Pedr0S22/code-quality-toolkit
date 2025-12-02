"""Vulnerable file to demonstrate plugins work"""

def calculate_price(user_formula: str):
    # VULNERABILITY: Using eval on untrusted input
    # A user could pass "__import__('os').system('rm -rf /')"
    result = eval(user_formula)
    return result

def get_user_data(username: str):
    # VULNERABILITY: Hardcoded SQL string with concatenation
    # If username is "' OR '1'='1", it dumps the whole database.
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return query