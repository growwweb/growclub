import sqlite3
import logging

class Database:
    def __init__(self, db_name='members.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Создание таблицы при первом запуске"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    name TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    username TEXT,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("База данных инициализирована")
        except Exception as e:
            logging.error(f"Ошибка инициализации БД: {e}")
    
    def add_member(self, date, name, contact, username, user_id):
        """Добавление нового участника"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO members (date, name, contact, username, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, name, contact, username, user_id))
            
            conn.commit()
            conn.close()
            logging.info(f"Участник {name} добавлен в БД")
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления участника: {e}")
            return False
    
    def get_all_members(self):
        """Получение всех участников"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM members ORDER BY created_at DESC')
            members = cursor.fetchall()
            
            conn.close()
            return members
        except Exception as e:
            logging.error(f"Ошибка получения участников: {e}")
            return []
    
    def get_member_count(self):
        """Получение количества участников"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM members')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except Exception as e:
            logging.error(f"Ошибка получения количества участников: {e}")
            return 0
