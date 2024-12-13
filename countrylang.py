import sqlite3
import requests
import matplotlib.pyplot as plt
import os

# Constants
API_URL = "https://restcountries.com/v3.1/all?fields=name,region,capital,landlocked,languages,continents,currencies"
DB_NAME = "data.db"
LANGUAGES_FILE = "txtfiles/languages_per_country.txt"
REGIONS_FILE = "txtfiles/countries_per_region.txt"

# Ensure necessary directories exist
if not os.path.exists("visualizations"):
    os.makedirs("visualizations")
if not os.path.exists("txtfiles"):
    os.makedirs("txtfiles")

# Database setup
def setup_database():
    """Set up SQLite database with two tables: countries and languages."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create countries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT,
            capital TEXT,
            continent TEXT,
            landlocked BOOLEAN,
            currency TEXT
        )
    ''')

    # Create languages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER,
            language_name TEXT,
            FOREIGN KEY (country_id) REFERENCES countries (id)
        )
    ''')

    conn.commit()
    conn.close()

# Fetch data from API
def fetch_data():
    """Fetch data from the REST Countries API."""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

# Insert data into the database
def insert_data(countries_data):
    """Insert countries and languages data into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for country in countries_data:
        # Extract country data
        name = country.get("name", {}).get("common", "Unknown")
        region = country.get("region", "Unknown")
        capital = ", ".join(country.get("capital", ["Unknown"]))
        continent = ", ".join(country.get("continents", ["Unknown"]))
        landlocked = country.get("landlocked", False)
        currencies = country.get("currencies", {})
        currency = ", ".join([f"{code} ({info['name']})" for code, info in currencies.items() if 'name' in info]) if currencies else "Unknown"

        # Check for duplicate entry
        cursor.execute('''
            SELECT id FROM countries WHERE name = ?
        ''', (name,))
        existing_country = cursor.fetchone()

        if existing_country:
            # Skip inserting if the country already exists
            print(f"Skipping duplicate country: {name}")
            continue

        # Insert into countries table
        cursor.execute('''
            INSERT INTO countries (name, region, capital, continent, landlocked, currency)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, region, capital, continent, landlocked, currency))

        country_id = cursor.lastrowid

        # Extract and insert languages
        languages = country.get("languages", {})
        for language in languages.values():
            cursor.execute('''
                INSERT INTO languages (country_id, language_name)
                VALUES (?, ?)
            ''', (country_id, language))

    conn.commit()
    conn.close()

# Calculate number of languages per country
def calculate_languages_per_country():
    """Calculate the number of languages per country and write to a file."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = '''
        SELECT countries.name, COUNT(languages.id) AS language_count
        FROM countries
        JOIN languages ON countries.id = languages.country_id
        GROUP BY countries.name
        ORDER BY language_count DESC;
    '''

    results = cursor.execute(query).fetchall()

    # Write results to file
    with open(LANGUAGES_FILE, "w") as file:
        file.write("Country, Language Count\n")
        for row in results:
            file.write(f"{row[0]}, {row[1]}\n")

    conn.close()
    print(f"Languages per country written to {LANGUAGES_FILE}")

    return results

# Calculate count of countries per region
def calculate_countries_per_region():
    """Calculate the number of countries per region and write to a file."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = '''
        SELECT region, COUNT(*) AS country_count
        FROM countries
        GROUP BY region
        ORDER BY country_count DESC;
    '''

    results = cursor.execute(query).fetchall()

    # Write results to file
    with open(REGIONS_FILE, "w") as file:
        file.write("Region, Country Count\n")
        for row in results:
            file.write(f"{row[0]}, {row[1]}\n")

    conn.close()
    print(f"Countries per region written to {REGIONS_FILE}")

    return results

# Visualize data: Languages per country
def visualize_languages_per_country(results):
    """Visualize the number of languages per country as a bar chart."""
    countries = [row[0] for row in results[:10]]  # Top 10 countries
    language_counts = [row[1] for row in results[:10]]

    plt.figure(figsize=(10, 6))
    plt.barh(countries, language_counts, color="skyblue")
    plt.xlabel("Number of Languages")
    plt.ylabel("Country")
    plt.title("Top 10 Countries by Number of Languages")
    plt.gca().invert_yaxis()  # Invert y-axis for better readability
    plt.tight_layout()
    plt.savefig("visualizations/languages_per_country.png")
    plt.show(block=True)

# Visualize data: Countries per region
def visualize_countries_per_region(results):
    """Visualize the number of countries per region as a pie chart."""
    regions = [row[0] for row in results]
    country_counts = [row[1] for row in results]

    plt.figure(figsize=(8, 8))
    plt.pie(country_counts, labels=regions, autopct="%1.1f%%", startangle=140, colors=plt.cm.tab20.colors)
    plt.title("Distribution of Countries by Region")
    plt.tight_layout()
    plt.savefig("visualizations/countries_per_region.png")
    plt.show(block=True)

# Main execution
if __name__ == "__main__":
    # Set up the database
    setup_database()

    # Fetch data from the API
    data = fetch_data()

    # Check how many countries are already in the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    existing_count = cursor.execute("SELECT COUNT(*) FROM countries").fetchone()[0]
    conn.close()

    # Limit data to the next 25 countries
    limited_data = data[existing_count:existing_count + 25]

    # Insert the limited data into the database
    insert_data(limited_data)

    print("Data insertion complete. Run the script multiple times to fetch more data.")

    # Perform calculations and write results to files
    languages_results = calculate_languages_per_country()
    regions_results = calculate_countries_per_region()

    # Visualize data
    visualize_languages_per_country(languages_results)
    visualize_countries_per_region(regions_results)
