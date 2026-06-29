A = True
def grade():
    while True:
     try:
          num = int(input("enter your grade: "))
          return num
     except ValueError:
         print("Please enter integers only.")

while A:
    num = grade()

    if num >= 90:
        print("A")
    elif num >= 80:
        print("B")
    elif num >= 70:
        print("C")
    elif num >= 60:
        print("D")
    else:
        print("F")
    x = input("Do you want to check again? (yes/no): ")
    if x.lower() != "yes":
            A = False
            print("Goodbye.")
    else:
            print("Trying again...")
