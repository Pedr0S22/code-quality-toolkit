import sys   # to be able to read the command line arguments

# Usage: python calculator.py <operation> <integer> <integer>
# example: python calculator + 2 3 

# each operation must be imported from a sub-folder provided by a distinct sub-group originating from their branch.
from our_add.our_add import our_add
from our_multiplication.our_multiplication import our_multiplication
# UNCOMENT each line below as each sub-group delivers its <operation> 
# from our_sub import our_subtract
# from our_mul import our_multiply
# from our_div import our_divide
# from our_rem import div-remainder # integer remainder of division
# from our_pow import our_power # n to the power of m
# if needed (because there may be more than five subgroups), create more operations

# intentionally leave one blank line before a def so that flake8 detects it (E302)

def main():
    # Check number of command line arguments

    if len(sys.argv) != 4:
        print("Number of arguments must be exactly three")  # 'python3' keyword can be ignored
    else:
        # Access and display individual arguments
        operation = sys.argv[1]
        first_arg = sys.argv[2]
        second_arg = sys.argv[3]
        
        '''
        # uncomment this block for feedback, comment for run-time tests
            print(f"operation: {operation}")
            print(f"first argument: {first_arg}")
            print(f"second argument: {second_arg}")
        '''

        # convert inputs to integers and perform the operation
        num1 = int(first_arg)
        num2 = int(second_arg)

        if operation == '+':
            print(f"{our_add(num1, num2)}")
        elif operation == '*':
            print(f"{our_multiplication(num1, num2)}")
            #           print(f"{num1} + {num2} = {our_add(num1, num2)}")
            
            # add more operations as they are integrated into the main branch
            '''
                elif operation == '-':
                    print(f"{num1} - {num2} = {our_subtract(num1, num2)}")
                elif operation == '*':
                    print(f"{num1} * {num2} = {our_multiply(num1, num2)}")
                elif operation == '/':
                    print(f"{num1} / {num2} = {our_divide(num1, num2)}")

                # add more operations, as they are merged into the main trunk
            '''
        else:
            print(f"Invalid operation: {operation}")


if __name__ == "__main__":
    main()
