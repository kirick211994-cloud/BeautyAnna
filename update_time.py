import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

try:
    cursor.execute("""
        ALTER TABLE clients
        ADD COLUMN time TEXT
    """)
    print("Поле time успешно добавлено!")
except sqlite3.OperationalError as e:
    print(e)

connection.commit()
connection.close()