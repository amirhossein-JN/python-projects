A = True
def check_hunger():
    while True:
        try:
            print("Welcome to the Hunger and Anger Checker!")
            hunger = int(input("Enter your hunger: "))
            anger = int(input("Enter your anger: "))
            return hunger, anger
        except ValueError:
            print("Please enter integers only.")

while A:
    hunger, anger = check_hunger()

    if hunger > 4 and anger > 4:
        print("You are hungry and angry")
    elif hunger > 4:
        print("You are hungry")
    elif anger > 4:
        print("You are angry")
    else:
        print("You are not hungry or angry")

    x = input("Do you want to check again? (yes/no): ")

    if x.lower() != "yes":
        A = False
        print("Goodbye.")
    else:
        print("Trying again...")
