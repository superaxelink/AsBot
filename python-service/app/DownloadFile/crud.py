import logging
import mysql.connector
from mysql.connector import Error
from DownloadFile import constants


def create_connection():
    try:
        connection = mysql.connector.connect(
            host=constants.host_name,
            port = constants.port,
            user=constants.user_name,
            password=constants.user_password,
            database=constants.db_name
        )

        if connection.is_connected() :
            return connection

        else:
            raise ConnectionError("Failed to connect to the database")    
    except Error as e:
        #print(f"Error while connecting to MySQL: {e}")
        raise

def reconnect(connection):
    if connection is None or not connection.is_connected():
        connection = create_connection()
        return connection
    return connection

def create_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY,
        nickname VARCHAR(100),
        creditos INT,
        rol VARCHAR(100), 
        plan VARCHAR(100), 
        soporte VARCHAR(100), 
        anti_spam_timeout INT
    )
    """)
    connection.commit()

def insert_data(connection, query, params=None):
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return cursor
    except Error as e:
        logging.error(f"The error '{e}' occurred")
        return None

def fetch_data(connection, query, params=None):
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    except Error as e:
        logging.error(f"The error '{e}' occurred")
        return None

def update_data(connection, query, params=None):
    cursor = connection.cursor()
    cursor.execute(query, params)
    connection.commit()
    return cursor.rowcount