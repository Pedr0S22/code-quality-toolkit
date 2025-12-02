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

""" duplicate class """
class Apple:
    def __init__(self):
        self.remaining_bites = 3

    def take_bite(self):
        if self.remaining_bites > 0:
            print("You take a bite of the apple.")
            self.remaining_bites -= 1
        else:
            print("The apple is already eaten up!")

    def eaten_by_animal(self, animal):
        self.remaining_bites = 0
        print("The apple has been eaten by an animal.")
