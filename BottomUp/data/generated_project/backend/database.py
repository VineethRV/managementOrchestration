import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_user(self, username, password):
        self.cursor.execute("INSERT INTO Users (username, password) VALUES (?, ?)", (username, password))
        self.conn.commit()

    def calculate(self, user_id, calculation):
        self.cursor.execute("INSERT INTO Calculations (user_id, calculation) VALUES (?, ?)", (user_id, calculation))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_history(self, calculation_id):
        self.cursor.execute("SELECT * FROM History WHERE calculation_id = ?", (calculation_id,))
        return self.cursor.fetchall()

    def add_to_favorites(self, user_id, calculation_id):
        self.cursor.execute("INSERT INTO Favorites (user_id, calculation_id) VALUES (?, ?)", (user_id, calculation_id))
        self.conn.commit()

    def close(self):
        self.conn.close()

class CalculatorDB:
    def __init__(self, db_name):
        self.db = Database(db_name)

    def create_user(self, username, password):
        self.db.create_user(username, password)

    def calculate(self, user_id, calculation):
        return self.db.calculate(user_id, calculation)

    def get_history(self, calculation_id):
        return self.db.get_history(calculation_id)

    def add_to_favorites(self, user_id, calculation_id):
        self.db.add_to_favorites(user_id, calculation_id)

    def close(self):
        self.db.close()

# === file: main.py ===

from calculator import CalculatorDB

def main():
    db = CalculatorDB("calculator.db")

    # Create a user
    db.create_user("john", "password123")

    # Calculate a value
    calculation_id = db.calculate(1, "2+2")

    # Get the history of a calculation
    history = db.get_history(calculation_id)

    # Add a calculation to favorites
    db.add_to_favorites(1, calculation_id)

    # Close the database
    db.close()

if __name__ == '__main__':
    main()
