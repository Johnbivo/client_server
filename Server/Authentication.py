"""This file contains function for authentication in login. The state machine can access these functions,
to determine if the credentials given by the client is correct and check if the user is an admin"""


import sqlite3
from threading import Lock
import ServerLogger


logger = ServerLogger.server_logger
lock = Lock()


def authenticate_user(username, password, manager_db="task_manager.db"):
    try:
        with lock: # Added a lock to prevent many threads from entering the database at the same time and creating conflict.
            conn = sqlite3.connect(manager_db)
            cursor = conn.cursor()


            # Query to check if the username and password match
            cursor.execute("""
                SELECT * FROM users WHERE Username = ? AND Password = ?
            """, (username, password))

            user = cursor.fetchone()
            logger.info(user)

            if user:
                logger.info("Authentication successful!")
                return True
            else:
                logger.warning("Invalid credentials.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def admin_right(username, manager_db="task_manager.db"):
    try:
        with lock: # Added a lock to prevent many threads from entering the database at the same time and creating conflict.
            conn = sqlite3.connect(manager_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Role FROM users WHERE Username = ?
            """, (username,))
            user = cursor.fetchone()

            if user and user[0] == "admin": # Fetchone returns a tuple. Check if the user exists and the first element of the tuple is 'admin'
                return True
            else:

                return False
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()



