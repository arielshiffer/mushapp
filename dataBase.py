import sqlite3

conn = sqlite3.connect('mushapp_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
table_exists = cursor.fetchone() is not None
if not table_exists:
    print('here')
    cursor.execute("""CREATE TABLE users (
                Name text,
                Password text,
                id integer,
                ip text
                )""")

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='songs'")
table_exists = cursor.fetchone() is not None
if not table_exists:
    cursor.execute("""CREATE TABLE songs (
                    Name text,
                    File text
                    )""")
    print('adding songs')
    cursor.execute("INSERT INTO songs VALUES ('in-da-club', '50 Cent - In Da Club (Official Music Video).mp3')")
    cursor.execute("INSERT INTO songs VALUES ('passionfruit', 'Drake - Passionfruit.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('flashing-lights', 'Flashing Lights.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('wet-dreamz', 'J. Cole - Wet Dreamz.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('billie-jean', 'Michael Jackson - Billie Jean (Official Video).mp3')")
    cursor.execute("INSERT INTO songs VALUES ('money-trees', 'Money Trees.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('runaway', 'Runaway.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('see-you-again', 'See You Again.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('stan', 'Stan.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('counting-stars', 'OneRepublic - Counting Stars.mp3')")
    cursor.execute("INSERT INTO songs VALUES ('shape-of-you', 'Ed Sheeran - Shape of You (Official Music Video).mp3')")
    cursor.execute("INSERT INTO songs VALUES ('hello', 'Adele - Hello (Official Music Video).mp3')")
    cursor.execute("INSERT INTO songs VALUES ('fly-me-to-the-moon', 'Fly Me To The Moon (2008 Remastered).mp3')")
    cursor.execute("INSERT INTO songs VALUES ('rockabye',"
                   " 'Clean Bandit - Rockabye (feat. Sean Paul & Anne-Marie) [Official Video].mp3')")
    cursor.execute("INSERT INTO songs VALUES ('wake-me-up', 'Avicii - Wake Me Up (Official Video).mp3')")


conn.commit()

conn.close()
