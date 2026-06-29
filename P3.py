A = True
while A == True:
    x = float(input("Enter your number: "))
   
    if x % 3 == 0 and x % 5 == 0:
        print("The number is divisible by 3 and 5.")
    elif x % 3 == 0:
        print("The number is divisible by 3.")
    elif x % 5 == 0:
        print("The number is divisible by 5.")
    else:
        print(x, "is not divisible by 3 or 5.")
    print("Do you want to try again? (yes/no)")
    answer = input().lower()
    if answer == "no":
        A = False
        print("Thank you for using the program!")
    if answer == "yes":
        A = True    