import random

num = random.randint(1, 10)

guess = 0
while guess != num :
    guess = int(input("enter your guess: "))
    if guess == num:
        print("got it")
    else:
        print("try agin")