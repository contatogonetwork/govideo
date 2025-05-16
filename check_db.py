import sqlite3
import os

def check_database():
    db_path = 'gonetwork.db'
    if not os.path.exists(db_path):
        db_path = os.path.join('data', 'gonetwork.db')
    
    print(f"Tentando abrir o banco de dados em: {os.path.abspath(db_path)}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Listar tabelas
    cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tabelas encontradas: {tables}")
    
    # Verificar atividades
    if 'activities' in tables:
        cur.execute('SELECT COUNT(*) FROM activities')
        count = cur.fetchone()[0]
        print(f"Total de atividades: {count}")
        
        cur.execute('SELECT id, name, stage_id FROM activities LIMIT 5')
        activities = cur.fetchall()
        print("\nAlgumas atividades:")
        for activity in activities:
            print(f"ID: {activity[0]}, Nome: {activity[1]}, Palco ID: {activity[2]}")
            
    # Verificar stages (palcos)
    if 'stages' in tables:
        cur.execute('SELECT COUNT(*) FROM stages')
        count = cur.fetchone()[0]
        print(f"\nTotal de palcos: {count}")
        
        cur.execute('SELECT id, name, event_id FROM stages LIMIT 5')
        stages = cur.fetchall()
        print("\nAlguns palcos:")
        for stage in stages:
            print(f"ID: {stage[0]}, Nome: {stage[1]}, Evento ID: {stage[2]}")
            
    # Verificar eventos
    if 'events' in tables:
        cur.execute('SELECT COUNT(*) FROM events')
        count = cur.fetchone()[0]
        print(f"\nTotal de eventos: {count}")
        
        cur.execute('SELECT id, name FROM events LIMIT 5')
        events = cur.fetchall()
        print("\nAlguns eventos:")
        for event in events:
            print(f"ID: {event[0]}, Nome: {event[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
