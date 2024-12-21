import random
import re
import pyodbc
from datetime import datetime

# Database connection
# conn = pyodbc.connect(
#     'DRIVER={ODBC Driver 17 for SQL Server};'
#     'SERVER=your_server_name;'
#     'DATABASE=banking_system;'
#     'UID=your_username;'
#     'PWD=your_password;'
# )
server = 'DESKTOP-U7RDVH2\\SQLEXPRESS'
database = 'Banking_System'
# Establish a connection to the SQL Server
conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes')

cursor = conn.cursor()

# Create tables
cursor.execute('''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    account_number NVARCHAR(10) UNIQUE NOT NULL,
    dob DATE NOT NULL,
    city NVARCHAR(50) NOT NULL,
    password NVARCHAR(50) NOT NULL,
    balance FLOAT NOT NULL CHECK(balance >= 2000),
    contact_number NVARCHAR(10) NOT NULL,
    email NVARCHAR(100) NOT NULL,
    address NVARCHAR(255) NOT NULL,
    is_active BIT DEFAULT 1
)''')

cursor.execute('''IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='transactions' AND xtype='U')
CREATE TABLE transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    account_number NVARCHAR(10) NOT NULL,
    type NVARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    date DATETIME NOT NULL
)''')

conn.commit()

# Utility functions
def validate_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

def validate_contact(contact):
    return re.match(r'^\d{10}$', contact)

def validate_password(password):
    return len(password) >= 8 and any(c.isdigit() for c in password) and any(c.isalpha() for c in password)

def generate_account_number():
    return str(random.randint(10**9, 10**10 - 1))

def validate_date(dob):
    try:
        datetime.strptime(dob, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Features
def add_user():
    while True:
        name = input("Enter name: ")
        dob = input("Enter date of birth (YYYY-MM-DD): ")
        city = input("Enter city: ")
        contact = input("Enter contact number: ")
        email = input("Enter email: ")
        address = input("Enter address: ")
        password = input("Enter password: ")
        initial_balance = input("Enter initial balance (minimum 2000): ")

        if not all([name, dob, city, contact, email, address, password, initial_balance]):
            print("All fields are mandatory. Please fill all fields.")
            continue

        if not validate_date(dob):
            print("Invalid date format. Please enter in YYYY-MM-DD format.")
            continue

        if not validate_contact(contact):
            print("Invalid contact number. Must be exactly 10 digits.")
            continue

        if not validate_email(email):
            print("Invalid email address.")
            continue

        if not validate_password(password):
            print("Password must be at least 8 characters long, include letters and numbers.")
            continue

        try:
            initial_balance = float(initial_balance)
            if initial_balance < 2000:
                print("Initial balance must be at least 2000.")
                continue
        except ValueError:
            print("Invalid balance. Please enter a numeric value.")
            continue

        account_number = generate_account_number()

        # Retry logic for account number uniqueness
        while True:
            try:
                cursor.execute(
                    '''INSERT INTO users (name, account_number, dob, city, password, balance, contact_number, email, address) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (name, account_number, dob, city, password, initial_balance, contact, email, address)
                )
                conn.commit()
                print(f"User added successfully! Account Number: {account_number}")
                break
            except pyodbc.IntegrityError:
                print("Account number collision detected. Regenerating account number.")
                account_number = generate_account_number()

        break


def show_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"\nID: {user[0]}\nName: {user[1]}\nAccount Number: {user[2]}\nDOB: {user[3]}\nCity: {user[4]}\nBalance: {user[6]}\nContact: {user[7]}\nEmail: {user[8]}\nAddress: {user[9]}\nActive: {'Yes' if user[10] else 'No'}")

def login():
    account_number = input("Enter account number: ")
    password = input("Enter password: ")

    cursor.execute("SELECT * FROM users WHERE account_number = ? AND password = ? AND is_active = 1", (account_number, password))
    user = cursor.fetchone()

    if user:
        print("Login successful.")
        while True:
            print("\n1. Show Balance\n2. Show Transactions\n3. Credit Amount\n4. Debit Amount\n5. Transfer Amount\n6. Activate/Deactivate Account\n7. Change Password\n8. Update Profile\n9. Logout")
            choice = int(input("Enter your choice: "))

            if choice == 1:
                cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))
                updated_balance = cursor.fetchone()[0]
                print(f"Your current balance is: {updated_balance}")

            elif choice == 2:
                cursor.execute("SELECT * FROM transactions WHERE account_number = ?", (account_number,))
                transactions = cursor.fetchall()
                for txn in transactions:
                    print(f"\nID: {txn[0]}\nType: {txn[2]}\nAmount: {txn[3]}\nDate: {txn[4]}")

            elif choice == 3:
                amount = float(input("Enter amount to credit: "))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (amount, account_number))
                cursor.execute("INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Credit', ?, ?)", (account_number, amount, datetime.now()))
                conn.commit()
                print("Amount credited successfully.")


            elif choice == 4:  # Debit Amount

                try:

                    amount = float(input("Enter amount to debit: "))

                    if amount <= 0:
                        print("Amount must be greater than 0.")

                        continue

                    # Fetch the latest balance from the database

                    cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))

                    current_balance = cursor.fetchone()[0]

                    if amount > current_balance:

                        print("Insufficient balance.")

                    else:

                        # Deduct the amount from the balance

                        cursor.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?",
                                       (amount, account_number))

                        # Record the transaction

                        cursor.execute(

                            "INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Debit', ?, ?)",

                            (account_number, amount, datetime.now())

                        )

                        conn.commit()

                        print(f"Amount debited successfully. Your new balance is: {current_balance - amount}")

                except ValueError:

                    print("Invalid input. Please enter a valid number.")

            elif choice == 5:

                target_account = input("Enter target account number: ")

                amount = float(input("Enter amount to transfer: "))

                # Fetch the balance of the user

                cursor.execute("SELECT balance FROM users WHERE account_number = ?", (account_number,))

                user_balance = cursor.fetchone()

                if user_balance is None:
                    print("Account not found.")

                    return

                if amount > user_balance[0]:
                    print("Insufficient balance.")

                    return

                # Check if the target account exists

                cursor.execute("SELECT balance FROM users WHERE account_number = ?", (target_account,))

                target_balance = cursor.fetchone()

                if target_balance is None:
                    print("Target account does not exist.")

                    return

                # Proceed with the transfer

                try:

                    # Begin transaction

                    cursor.execute("BEGIN TRANSACTION")

                    # Deduct from the sender

                    cursor.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?", (amount, account_number))

                    # Add to the receiver

                    cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (amount, target_account))

                    # Record the transaction for sender

                    cursor.execute("INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Transfer', ?, ?)",

                                   (account_number, amount, datetime.now()))

                    # Record the transaction for receiver

                    cursor.execute("INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Receive', ?, ?)",

                                   (target_account, amount, datetime.now()))

                    # Commit the transaction

                    conn.commit()

                    print("Amount transferred successfully.")


                except Exception as e:

                    # Handle potential errors and rollback if anything goes wrong

                    print(f"An error occurred: {e}")

                    conn.rollback()



            elif choice == 6:

                # Fetch the current status of the account

                cursor.execute("SELECT is_active FROM users WHERE account_number = ?", (account_number,))

                account_status = cursor.fetchone()

                if account_status is None:
                    print("Account not found.")

                    return

                current_status = account_status[0]

                # Toggle account status (active -> inactive, inactive -> active)

                new_status = 0 if current_status else 1

                # Update the account's active status in the database

                cursor.execute("UPDATE users SET is_active = ? WHERE account_number = ?", (new_status, account_number))

                conn.commit()

                if new_status == 1:

                    print("Account activated successfully.")

                else:

                    print("Account deactivated successfully.")


            elif choice == 7:
                new_password = input("Enter new password: ")
                if validate_password(new_password):
                    cursor.execute("UPDATE users SET password = ? WHERE account_number = ?", (new_password, account_number))
                    conn.commit()
                    print("Password updated.")
                else:
                    print("Invalid password format.")

            elif choice == 8:
                new_city = input("Enter new city: ")
                new_contact = input("Enter new contact number: ")
                new_email = input("Enter new email: ")
                new_address = input("Enter new address: ")

                if validate_contact(new_contact) and validate_email(new_email):
                    cursor.execute("UPDATE users SET city = ?, contact_number = ?, email = ?, address = ? WHERE account_number = ?",
                                   (new_city, new_contact, new_email, new_address, account_number))
                    conn.commit()
                    print("Profile updated.")
                else:
                    print("Invalid contact or email.")

            elif choice == 9:
                print("Logged out successfully.")
                break

            else:
                print("Invalid choice.")
    else:
        print("Invalid account number or password, or account is inactive.")

def main():
    while True:
        print("\n1. Add User\n2. Show Users\n3. Login\n4. Exit")
        choice = int(input("Enter your choice: "))

        if choice == 1:
            add_user()
        elif choice == 2:
            show_users()
        elif choice == 3:
            login()
        elif choice == 4:
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()

# Close the database connection on exit
conn.close()
