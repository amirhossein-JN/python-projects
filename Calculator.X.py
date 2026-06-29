import math

print("=" * 40)
print("      Python Calculator")
print("=" * 40)
print("Supported operations:")
print("+  -  *  /  %  **")
print("sqrt(number)")
print("Example: 5+3*2")
print("Example: (10+5)/3")
print("Example: sqrt(81)+2")
print("Type 'exit' to quit.")
print("=" * 40)

allowed = {
    "__builtins__": None,
    "sqrt": math.sqrt
}

while True:
    expression = input("\nEnter expression: ")

    if expression.lower() == "exit":
        print("Goodbye!")
        break

    try:
        result = eval(expression, allowed)
        print("Result =", result)

    except ZeroDivisionError:
        print("Error: Division by zero.")

    except ValueError:
        print("Error: Invalid value.")

    except SyntaxError:
        print("Error: Invalid expression.")

    except NameError:
        print("Error: Unsupported function or text.")

    except Exception:
        print("Error: Invalid input.")