import sqlite3

conn = sqlite3.connect('user.db')
print ("Opened database successfully")

# conn.execute('CREATE TABLE students (name TEXT, addr TEXT, city TEXT, pin TEXT)')
conn.execute("CREATE TABLE users (id INTEGER, email TEXT NOT NULL, user_name TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(id))")
print ("Table created successfully")
conn.close()
