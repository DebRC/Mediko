from dotenv import load_dotenv
import psycopg2
import os
import csv

load_dotenv()

def connect_to_db():
    conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    database=os.getenv("POSTGRES_DATABASE"),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'))

    return conn

def init_db(conn):
    response=initCustomerAuthTable(conn)
    if(response["res"]==0):
        return {"res": 0, "message": "INIT customerAuth Failure"}
    response=initMedicineDatabase(conn)
    if(response["res"]==0):
        return {"res": 0, "message": "INIT MedicineDB Failure"}
    return {"res": 1, "message": "INIT Success"}

def insert(conn, table, data):
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                return {"res": 1, "message": "Insertion Success"}
    except:
        return {"res": 0, "message": "Insertion Failure"}
    

def select(conn, table, columns=None, condition=None, desc=False):
    if columns:
        columns_str = ', '.join(columns)
    else:
        columns_str = '*'

    query = f"SELECT {columns_str} FROM {table}"
    
    if condition:
        query += f" WHERE {condition}"
    if desc:
        query += f" ORDER BY DESC"

    query+=";"
    print(query)
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                if(len(result)==0):
                    return {"res": 0, "message": "Selection Success: NULL Result"}
                else:
                    return {"res": 1, "message": "Selection Success: Valid Result", "result": result[0]}
    except:
        return {"res": 0, "message": "Selection Failure"}
    

def initCustomerAuthTable(conn):
    query = '''
    CREATE TABLE IF NOT EXISTS customerAuth 
    (username TEXT PRIMARY KEY, password TEXT);'''
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
        return {"res": 1, "message": "Table Creation Successful"}
    except:
        return {"res": 0, "message": "Table Creation Unsuccessful"}

def initMedicineDatabase(conn):
    query = '''CREATE TABLE IF NOT EXISTS medicines
      (id SERIAL PRIMARY KEY,
       name TEXT NOT NULL,
       composition TEXT NOT NULL,
       price TEXT NOT NULL,
       manufacturer TEXT,
       description TEXT,
       category TEXT,
       side_effects TEXT);'''
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
    except:
        return {"res": 0, "message": "Table Creation Unsuccessful"}
    # response=select(conn, table="medicines")

    query = '''SELECT COUNT(*) FROM medicines;'''
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                if(cursor.fetchone()[0]!=0):
                    return {"res": 1, "message": "Table Creation Successful"}
    except:
        return {"res": 0, "message": "Table Creation Unsuccessful"}

    medFile=open("extras/medicine_data.csv", mode="r", newline="")
    medFileReader=csv.reader(medFile)
    next(medFileReader)
    for row in medFileReader:
        price=row[3]
        if(price==""):
            price="50"
        data={
            "category":row[0],
            "name":row[1],
            "composition":row[2],
            "price":price,
            "manufacturer":row[4],
            "description":row[5],
            "side_effects":row[6],
        }
        response=insert(conn,"medicines",data)
        if(response["res"]==0):
            query = '''DROP TABLE medicines;'''
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
            return {"res": 0, "message": "Table Creation Unsuccessful"}
    return {"res": 1, "message": "Table Creation Successful"}
    
    