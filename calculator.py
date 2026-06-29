import math
A = True
def calculator():
    while True:
        try:
            num1 = float(input("Enter the first number: "))

            while True:
                operator = input("Enter the operator (+, -, *, /, **, sqrt): ")
                if operator in ["+", "-", "*", "/", "**", "sqrt"]:
                    break
                print("Invalid operator. Please enter one of: +, -, *, /, **, sqrt.")

            if operator == "sqrt":
                return num1, operator, None

            num2 = float(input("Enter the second number: "))
            return num1, operator, num2

        except ValueError:
            print("Please enter valid numbers.")

while A:
    num1, operator, num2 = calculator()

    if operator == "+":
        result = num1 + num2

    elif operator == "-":
        result = num1 - num2

    elif operator == "*":
        result = num1 * num2

    elif operator == "/":
        if num2 != 0:
            result = num1 / num2
        else:
            print("Error: Division by zero.")
            continue

    elif operator == "**":
        result = num1 ** num2

    elif operator == "sqrt":
        if num1 >= 0:
            result = math.sqrt(num1)
        else:
            print("Error: Cannot calculate the square root of a negative number.")
            continue

    print(f"The result is: {result}")

    x = input("Do you want to calculate again? (yes/no): ")

    if x.lower() != "yes":
        A = False
        print("Goodbye!")
    else:
        print("Trying again...")