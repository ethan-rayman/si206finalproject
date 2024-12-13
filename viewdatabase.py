import sqlite3

# Database file path
DATABASE = "data.db"

def view_data1():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    rows = cursor.fetchall()
    print("Data in the 'movies' table:")
    for row in rows:
        print(row)
    conn.close()

def view_data2():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries")
    rows = cursor.fetchall()
    print("Data in the 'countries' table:")
    for row in rows:
        print(row)
    conn.close()


def view_data3():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM languages")
    rows = cursor.fetchall()
    print("Data in the 'languages' table:")
    for row in rows:
        print(row)
    conn.close()

def view_data4():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    print("Data in the 'books' table:")
    for row in rows:
        print(row)
    conn.close()

def view_data5():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authors")
    rows = cursor.fetchall()
    print("Data in the 'books' table:")
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    view_data1()
    view_data2()
    view_data3()
    view_data4()
    view_data5()
