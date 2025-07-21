"""This is the database of the task manager application. It stores user and tasks in 2 different tables
that are connected with UserID. Notice that a task must be assigned to an existing user.


The database has functions to support the functionality of the task manager. The task manager app uses CRUD
(Create, Read, Update, Delete). The admins can also view users.

The database did not need to be in a class. Its just more organized.


Admin accounts can be created only via this file."""



import sqlite3
from threading import Lock
import ServerLogger

class Database:
    def __init__(self, manager_db):
        self.manager_db = manager_db
        self.lock = Lock()
        self.logger = ServerLogger.server_logger

    def connect(self):
        return sqlite3.connect(self.manager_db)


    def create_table_users(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                                                            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            Username VARCHAR(50) NOT NULL,
                                                            Password VARCHAR(50) NOT NULL,
                                                            Role TEXT CHECK(ROLE IN ('admin', 'user')) DEFAULT 'user',
                                                            AccountCreatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

        conn.commit()
        cursor.close()
        conn.close()



    def create_table_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS tasks(
                                                            TaskID INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            TaskDescription VARCHAR(100) NOT NULL,
                                                            DateOfCreation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                            DueDate DATE,
                                                            Active BOOLEAN DEFAULT True,
                                                            Created_by INT NOT NULL,
                                                            Assigned_to INT NOT NULL,
                                                            FOREIGN KEY (Created_by) REFERENCES users(UserID),
                                                            FOREIGN KEY (Assigned_to) REFERENCES users(UserID))""")
        conn.commit()
        cursor.close()
        conn.close()

    def insert_user(self, username, password, role='user'):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            with self.lock:
                cursor.execute("SELECT UserID FROM users WHERE Username = ?", (username,))
                if cursor.fetchone():
                    return "User already exists"

                cursor.execute("""INSERT INTO users (Username, Password, Role) VALUES (?, ?, ?)""",
                               (username, password, role))
                conn.commit()
                return "Success"
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            return "Error"
        finally:
            cursor.close()
            conn.close()

    def insert_task(self, task_description, due_date, active, assigned_to =None, created_by=None):
        if assigned_to == None:
            assigned_to = created_by
        assigned_to = self.get_userID_fromDB(assigned_to)
        try:
            with self.lock:  # Ensure thread-safe operations
                conn = self.connect()
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO tasks (TaskDescription, DueDate, active, Created_by, Assigned_to) 
                                  VALUES (?, ?, ?, ?, ?)""",
                               (task_description, due_date, active, created_by, assigned_to))
                conn.commit()
                return "Success"
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            return "Error"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_userID_fromDB(self, username):
        try:
            self.logger.debug("Getting user ID from database")
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT UserID FROM users WHERE Username = ?", (username,))
            result = cursor.fetchone()
            if result:
                self.logger.debug(f"Found UserID: {result[0]}")
                return result[0]
            else:
                self.logger.debug("User not found")
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()




    def delete_task(self,TaskID):
        conn = self.connect()
        cursor = conn.cursor()
        task_id_number = int(TaskID)
        try:
            with self.lock:
                cursor.execute("DELETE FROM tasks WHERE TaskID = ?", (task_id_number,))
                conn.commit()
            self.logger.info(f"Successfully deleted task with taskID {task_id_number}")
            return "Success"
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
        finally:
            cursor.close()
            conn.close()

    def show_tasks(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            with self.lock:
                # Select only essential fields and join with users table to get usernames
                cursor.execute("""
                    SELECT 
                        t.TaskID,
                        t.TaskDescription,
                        t.DueDate,
                        t.Active,
                        u1.Username as AssignedToUsername
                    FROM tasks t
                    LEFT JOIN users u1 ON t.Assigned_to = u1.UserID
                    ORDER BY t.TaskID DESC
                """)
                conn.commit()
                result = cursor.fetchall()

                if not result:
                    self.logger.info("No tasks found in database")
                    return None

                # Convert to list of compact dictionaries
                tasks = []
                for task in result:
                    try:
                        task_dict = {
                            "TaskID": str(task[0]),
                            "Description": str(task[1])[:50],
                            "due_date": str(task[2]) if task[2] else "",
                            "active": "1" if task[3] else "0",
                            "assigned_to": str(task[4]) if task[4] else ""
                        }
                        tasks.append(task_dict)
                    except Exception as e:
                        self.logger.error(f"Error processing task row {task}: {e}")
                        continue

                return tasks

        except sqlite3.Error as e:
            self.logger.error(f"Database error in show_tasks: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    def update_task(self, task_id, description, due_date, active, assigned_to, updated_by):
        try:
            with self.lock:
                conn = self.connect()
                cursor = conn.cursor()

                # Get the assigned_to user ID
                assigned_to_id = self.get_userID_fromDB(assigned_to)
                if not assigned_to_id:
                    return "Failed"

                cursor.execute("""
                    UPDATE tasks 
                    SET TaskDescription = ?, 
                        DueDate = ?, 
                        Active = ?,
                        Assigned_to = ?
                    WHERE TaskID = ?
                """, (description, due_date, active, assigned_to_id, task_id))

                conn.commit()
                return "Success"
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            return "Failed"
        finally:
            cursor.close()
            conn.close()

    def show_users(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            with self.lock:
                cursor.execute("""SELECT Username, Role FROM users ORDER BY Username""")
                result = cursor.fetchall()

                if not result:
                    self.logger.info("No users found in database")
                    return None
                users = []
                for user in result:
                    try:
                        user_dict = {
                            "username": str(user[0]),
                            "role": str(user[1])
                        }
                        users.append(user_dict)
                    except Exception as e:
                        self.logger.error(f"Error processing user row {user}: {e}")
                        continue

                return users

        except sqlite3.Error as e:
            self.logger.error(f"Database error in show_users: {e}")
            return None
        finally:
            cursor.close()
            conn.close()






