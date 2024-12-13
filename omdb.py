import sqlite3
import json
from datetime import datetime
import requests
import time
import os
import matplotlib.pyplot as plt

DATABASE = "data.db"
OUTPUT_FILE = "txtfiles/averageratingbygenre.txt"
API_KEY = '61d16990'
BASE_URL = 'http://www.omdbapi.com/'

def makedb():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        imdb_id TEXT UNIQUE,
        title TEXT,
        year TEXT,
        genre TEXT,
        director TEXT,
        actors TEXT,
        imdb_rating REAL,
        box_office TEXT,
        runtime TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def getAPImovies(page):
    parameters = {"s": "movie", "apikey": API_KEY, "page": page}
    response = requests.get(BASE_URL, params=parameters)
    data = response.json()
    
    if data.get("Response") == "True":
        return data["Search"]

def getAPImoviedetails(imdb_id):
    parameters = {"i": imdb_id, "apikey": API_KEY}
    response = requests.get(BASE_URL, params=parameters)
    data = response.json()
    
    if data.get("Response") == "True":
        return data

def savetodb(movies):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    for movie in movies:
        imdbdetails = getAPImoviedetails(movie["imdbID"])
        
        cursor.execute('''
        INSERT OR IGNORE INTO movies (
            imdb_id, title, year, genre, director, actors, imdb_rating, box_office, runtime
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            imdbdetails["imdbID"],
            imdbdetails["Title"],
            imdbdetails["Year"],
            imdbdetails["Genre"],
            imdbdetails["Director"],
            imdbdetails["Actors"],
            float(imdbdetails.get("imdbRating", 0)) if imdbdetails.get("imdbRating") else None,
            imdbdetails["BoxOffice"],
            imdbdetails["Runtime"]
        ))

    conn.commit()
    conn.close()

def genrestats():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    query = '''
    SELECT genre, imdb_rating
    FROM movies
    WHERE genre IS NOT NULL AND imdb_rating IS NOT NULL
    '''

    cursor.execute(query)
    rows = cursor.fetchall()
    genrerating = {}
    genrecount = {}

    for row in rows:
        genres = []
        for genre in row[0].split(","):
            genres.append(genre.strip())
        rating = row[1]
        for genre in genres:
            if genre not in genrerating:
                genrerating[genre] = []
            if genre not in genrecount:
                genrecount[genre] = 0
            genrerating[genre].append(rating)
            genrecount[genre] += 1

    avg_ratings = [(genre, sum(ratings) / len(ratings), genrecount[genre]) for genre, ratings in genrerating.items()]
    avg_ratings.sort(key=lambda x: x[1], reverse=True)

    conn.close()
    return avg_ratings

def writetotxt(data):
    with open(OUTPUT_FILE, "w") as file:
        file.write("Genre, Average IMDb Rating, Frequency\n")
        for genre, avg_rating, count in data:
            file.write(f"{genre}, {avg_rating:.2f}, {count}\n")

def makebarchart():
    calcdata = genrestats()
    genres = []
    avratings = []
    for ent in calcdata:
        genres.append(ent[0])
        avratings.append(ent[1])

    plt.figure(figsize=(10, 6))
    plt.bar(genres, avratings, color="blue")
    plt.title('Average IMDb Rating by Genre')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Genre')
    plt.ylabel('Average IMDb Rating')
    plt.tight_layout()
    plt.savefig("visualizations/barchart_ratings_by_genre.png")
    plt.show()

def makepiechart():
    calcdata = genrestats()
    genres = []
    freq = []
    for ent in calcdata:
        genres.append(ent[0])
        freq.append(ent[2])

    plt.figure(figsize=(8, 8))
    plt.pie(freq, labels=genres, autopct='%d%%')
    plt.title('Genre Frequency')
    plt.tight_layout()
    plt.savefig("visualizations/piechart_genre_frequency.png")
    plt.show()

def main():
    makedb()
    page = 1

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    currcount = cursor.fetchone()[0]
    conn.close()

    entrylimit = 20
    entrycount = 0

    while entrycount < entrylimit:
        movies = getAPImovies(page)
        savetodb(movies)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movies")
        newcount = cursor.fetchone()[0]
        entrycount = newcount - currcount
        conn.close()
        page += 1
        time.sleep(.5)

    makebarchart()
    makepiechart()

if __name__ == "__main__":
    main()
