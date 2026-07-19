import sqlite3

def run():
    conn = sqlite3.connect('multiagent.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM biblio_researchers WHERE scholar_id = 'qc6CJjYAAAAJ'")
    conn.commit()
    conn.close()
    print('Deleted test account')

if __name__ == "__main__":
    run()
