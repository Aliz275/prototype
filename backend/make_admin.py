import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute("UPDATE users SET is_admin = 1 WHERE email = ?", ('alihabibi2299@gmail.com',))
conn.commit()
conn.close()

print("Admin account updated!")
