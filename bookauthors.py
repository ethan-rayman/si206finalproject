import sqlite3
import requests
import json
import matplotlib.pyplot as plt

# Constants
API_URL = "https://openlibrary.org/search.json"
DB_NAME = "data.db"
BATCH_SIZE = 25
BOOKS_FILE = "txtfiles/books_per_year.txt"

# Database setup
def setup_database():
    """Set up SQLite database with tables: books and authors."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER,
            first_publish_year INTEGER,
            isbn TEXT,
            language TEXT,
            subject TEXT,
            FOREIGN KEY (author_id) REFERENCES authors (id)
        )
    ''')

    # Create authors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    conn.commit()
    conn.close()

# Fetch data from API
def fetch_data(query, offset=0):
    """Fetch data from the Open Library API with pagination."""
    try:
        params = {"q": query, "limit": BATCH_SIZE, "offset": offset}
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("docs", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

# Insert data into the database
def insert_data(books_data):
    """Insert book and author data into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for book in books_data:
        # Extract book data
        title = book.get("title", "Unknown")
        authors = book.get("author_name", ["Unknown"])
        first_publish_year = book.get("first_publish_year", None)
        isbn = ", ".join(book.get("isbn", ["Unknown"]))[:13]
        language = ", ".join(book.get("language", ["Unknown"]))
        subject = ", ".join(book.get("subject", ["Unknown"]))

        # Insert authors and get their IDs
        for author in authors:
            cursor.execute('''
                INSERT OR IGNORE INTO authors (name) VALUES (?)
            ''', (author,))
            cursor.execute('''
                SELECT id FROM authors WHERE name = ?
            ''', (author,))
            author_id = cursor.fetchone()[0]

            # Check for duplicate entry
            cursor.execute('''
                SELECT id FROM books WHERE title = ? AND author_id = ?
            ''', (title, author_id))
            existing_book = cursor.fetchone()

            if existing_book:
                print(f"Skipping duplicate book: {title} by {author}")
                continue

            # Insert into books table
            cursor.execute('''
                INSERT INTO books (title, author_id, first_publish_year, isbn, language, subject)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, author_id, first_publish_year, isbn, language, subject))

    conn.commit()
    conn.close()

# Export data to JSON
def export_to_json():
    """Export data from the database to a JSON file."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT books.title, authors.name, books.first_publish_year, books.isbn, books.language, books.subject
        FROM books
        JOIN authors ON books.author_id = authors.id
    ''')
    books = cursor.fetchall()
    with open("books_data.json", "w") as f:
        json.dump(books, f, indent=4)
    conn.close()

# Visualization
def create_visualizations():
    """Create visualizations from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Books by publication year
    cursor.execute('''
        SELECT first_publish_year, COUNT(*) FROM books
        WHERE first_publish_year IS NOT NULL
        GROUP BY first_publish_year
        ORDER BY first_publish_year
    ''')
    data = cursor.fetchall()
    years, counts = zip(*data)

    with open(BOOKS_FILE, "w") as file:
        file.write("Year, Book Count\n")
        for row in data:
            file.write(f"{row[0]}, {row[1]}\n")

    plt.bar(years, counts)
    plt.xlabel("Publication Year")
    plt.ylabel("Number of Books")
    plt.title("Books by Publication Year")
    plt.savefig("visualizations/barchart_books_by_year.png")
    plt.show()

    conn.close()

# Main execution
if __name__ == "__main__":
    # Set up the database
    setup_database()

    # Example queries to fetch
    queries = ["fiction", "history"]

    for query in queries:
        print(f"Fetching data for query: {query}...")

        # Determine how many records already exist in the database for this query
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        existing_count = cursor.fetchone()[0]
        conn.close()

        # Fetch and insert data in batches of BATCH_SIZE
        data = fetch_data(query, offset=existing_count)
        if data:
            insert_data(data)
            print(f"Data for query '{query}' inserted successfully.")
        else:
            print(f"No new data found for query: {query}.")

    # Export data to JSON
    print("Exporting data to JSON...")
    export_to_json()
    print("Data export complete. Run the script multiple times to gather more data.")

    # Create visualizations
    print("Creating visualizations...")
    create_visualizations()
    print("Visualizations complete.")
