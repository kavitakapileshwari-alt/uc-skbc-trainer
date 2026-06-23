import sqlite3
from datetime import datetime

DB_NAME = "uc_training.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_email TEXT,
            timestamp TEXT,
            module_tested TEXT,
            overall_score INTEGER,
            greeting_score INTEGER,
            empathy_score INTEGER,
            probing_score INTEGER,
            sop_score INTEGER,
            compliance_score INTEGER,
            communication_score INTEGER,
            closure_score INTEGER,
            coaching_feedback TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_evaluation(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evaluations (
            agent_email, timestamp, module_tested, overall_score,
            greeting_score, empathy_score, probing_score, sop_score,
            compliance_score, communication_score, closure_score, coaching_feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['agent_email'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data['module_tested'], data['overall_score'],
        data['greeting_score'], data['empathy_score'], data['probing_score'],
        data['sop_score'], data['compliance_score'], data['communication_score'],
        data['closure_score'], data['coaching_feedback']
    ))
    conn.commit()
    conn.close()
