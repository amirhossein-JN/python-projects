import random

def get_score():
    score = random.randint(0, 100)
    if score > 90:
        return f"Your score is {score} and you got an A!"
    elif score >= 80:
        return f"Your score is {score} and you got a B."
    else:
        return f"Your score is {score} and you failed."

print(get_score())