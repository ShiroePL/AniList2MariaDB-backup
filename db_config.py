import api_keys
import mysql.connector
host_name = api_keys.host_name
db_name = api_keys.db_name
user_name = api_keys.user_name
db_password = api_keys.db_password

# Define the global connection object
try:
    conn = mysql.connector.connect(host = host_name,
                                         database = db_name,
                                         user = user_name,
                                         password = db_password)
    if conn.is_connected():
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        record = cursor.fetchone()
        print("Connected to MySQL, server response:", record)

except Error as e:
    print("Error while connecting to MySQL", e)

