import json
import os

class PasswordManager:
    def __init__(self):
        self.file_name = "passwords.json"
        self.passwords = self.load_passwords()

    def load_passwords(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, "r") as file:
                return json.load(file)
        return {}

    def save_passwords(self):
        with open(self.file_name, "w") as file:
            json.dump(self.passwords, file, indent=4)

    def add_password(self):
        website = input("Website: ")
        username = input("Username: ")
        password = input("Password: ")

        self.passwords[website] = {
            "username": username,
            "password": password
        }

        self.save_passwords()
        print("\nPassword saved successfully.")

    def view_passwords(self):
        if not self.passwords:
            print("\nNo passwords saved.")
            return

        print("\nSaved Accounts:\n")

        for website, info in self.passwords.items():
            print(f"Website : {website}")
            print(f"Username: {info['username']}")
            print(f"Password: {info['password']}")
            print("-" * 30)

    def search_password(self):
        website = input("Enter website: ")

        if website in self.passwords:
            info = self.passwords[website]

            print("\nAccount Found")
            print(f"Username: {info['username']}")
            print(f"Password: {info['password']}")
        else:
            print("\nWebsite not found.")

    def delete_password(self):
        website = input("Enter website to delete: ")

        if website in self.passwords:
            del self.passwords[website]
            self.save_passwords()
            print("\nPassword deleted.")
        else:
            print("\nWebsite not found.")

def main():

    manager = PasswordManager()

    while True:

        print("\n========== Password Manager ==========")
        print("1. Add Password")
        print("2. View Passwords")
        print("3. Search Password")
        print("4. Delete Password")
        print("5. Exit")

        choice = input("Choose: ")

        if choice == "1":
            manager.add_password()

        elif choice == "2":
            manager.view_passwords()

        elif choice == "3":
            manager.search_password()

        elif choice == "4":
            manager.delete_password()

        elif choice == "5":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice.")

if __name__ == "__main__":
    main()