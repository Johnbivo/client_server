"""This file is the brains of the application. Every message and functionality is handled here.
The state machine handles logins, signups and CRUD (Create,Read,Update,Delete) operations. The client
upon starting the connection must first login/ if he has no account, must register first.(signup). If he
successfully signs in, he accesses dashboard functionality CRUD. Admins have an extra show users functionality.


The state machine structures and receives messages with the Client state machine. Both are configured to send and
receive  standard messages such as 'action':'Create Task' , 'message' : 'a message,dict'

The state machine changes states as the client moves uppon the proccess from signup/signin -> dashboard.
The state machine doesnt let the client access the dashboard if he hasnt logged in.


The state machine interacts with all of the files of the server, it authenticates users and admins through authentication.py ,
it gets and puts data into the database, writes logs, interacts with server and connectionhandler.


Note: The exit state has not been used.

"""




from enum import Enum
import ServerLogger
from Authentication import authenticate_user, admin_right
import Database
import Encryption



class State(Enum):
    Start = 1
    LoggingIn = 2
    SignUp = 3
    Dashboard = 4
    AdminDashboard = 5
    Exit = 6


class StateMachine:
    def __init__(self,connection_handler,client_public_key, server):
        self.currentState = State.Start
        self.previousState = None
        self.db = Database.Database("task_manager.db")
        self.logger = ServerLogger.server_logger
        self.connectionHandler = connection_handler
        self.client_public_key = client_public_key
        self.server = server
        self.rsaEncryption = Encryption.RsaEncryption()
        self.md5Encryption = Encryption.HashEncryption()
        self.caesarCipher = Encryption.CaesarCipher()



    def authenticate(self,username, password):
        """Handles authentication"""
        if authenticate_user(username=username, password=password): # database authentication
            self.logger.info(f"Login performed successfully by {username}")
            return "Success"
        else:
            self.logger.error("Login failed. Wrong username or password.")
            return "Failed"


    def handle_login(self, username, password):
        """Handles login"""
        authentication = self.authenticate(username, password)
        self.logger.info(f"Authentication result: {authentication}")
        if authentication == "Success":
            self.logger.info(f"{username} successfully logged in...")
            admin = self.handle_admin_rights(username)
            if admin == "Granted":
                self.logger.info(f"Admin rights granted for {username}")
                self.currentState = State.AdminDashboard
                access = {"action": "Login",
                          "message": "Provide Admin Access"}
            else:
                self.logger.info(f"Admin rights not granted for {username}")
                self.currentState = State.Dashboard
                access = {"action": "Login",
                          "message": "Provide Access"}

            self.logger.info(f"Pushing access message to client: {access}")
            self.connectionHandler.pushMessage(access)
        else:
            self.logger.info("Login failed")
            fail_message = {"action": "Login", "message": "Failed"}
            self.currentState = State.Start
            self.connectionHandler.pushMessage(fail_message)


    # Takes the usernameas argument and calls admin_right function from the Authentication.py -> Bool
    def handle_admin_rights(self,username):
        """Handles admin rights"""
        if admin_right(username=username):
            self.logger.info(f"Admin rights granted to {username} Opening AdminDashboard.")

            return "Granted"
        else:
            self.logger.info(f"Admin rights not granted to {username} Opening Dashboard.")
            return "Failed"
    def handle_signup(self,username,password):
        """Handles signup"""
        self.currentState = State.SignUp
        self.previousState = State.LoggingIn
        try:
            self.logger.debug(f"Username: {username}, Password: {password} sent to the database.")
            done = self.db.insert_user(username=username,password=password)
            if done == "Success":
                self.logger.info("New user {username} added the database.".format(username=username))
                self.currentState = State.Start
                self.previousState = State.SignUp
                self.logger.info("User Added")

                self.connectionHandler.pushMessage({"action": "SignUp",
                                                    "message": "Success"})
            elif done == "User already exists":
                self.currentState = State.Start
                self.connectionHandler.pushMessage({"action":"signup",
                                                    "message":"User already exists"})
                self.logger.info("User already exists")
            else:
                self.currentState = State.Start
                self.connectionHandler.pushMessage({"action": "signup",
                                                    "message": "Error"})
                self.logger.error("Error creating user")

        except Exception as e:
            self.logger.error(f"Error while creating new user {username}: {e}")
            self.connectionHandler.pushMessage({"action": "signup",
                                                "message": "Error"})

        finally:
            self.currentState = State.Start


    def handle_action(self,data):
        """Handles action"""
        action = data["action"]
        self.logger.debug(f"Received data: {data}")
        self.logger.debug(f"Received action: {action}")
        if self.currentState == State.Start:
            if action == "login":
                username = data["username"]
                password = data["password"]
                self.handle_login(username, password)
            elif action == "signup":
                username = data["username"]
                password = data["password"]
                self.handle_signup(username, password)

            else:
                self.logger.error("Invalid action at the start of the client. In start state, only login or signup is available. The client will now close")
                message = {"action": "Exit",
                           "message": "Exiting...An error occured during start."}

                self.connectionHandler.pushMessage(message)
                self.server.close_client(self.connectionHandler)

        elif self.currentState == State.Dashboard or self.currentState == State.AdminDashboard:
            message =data.get("message", {})
            username = data.get("username")
            self.process(action,message,username)

        else:
            self.logger.warning("Login required to continue.")





    def process(self,action,message,username):
        """The main functionality of the program after authentication(login/signup)"""
        self.logger.info("State Machine Started")
        if self.currentState == State.Dashboard:
            self.currentState = State.Dashboard
            self.previousState = State.LoggingIn
            self.logger.info(f"State changed to {self.currentState}")
            if action == "Create Task":
                if isinstance(message, dict):
                    self.logger.info(f"Creating task: {message}")
                    self.createTask(message)
            elif action == "Update Task":
                if isinstance(message, dict): #wont process client response of success or failed
                    self.update_task(message, username)
            elif action == "Delete Task":
                if isinstance(message, str) and message == "Success":
                    self.logger.info("Delete task operation was successful")
                    self.show_tasks()
                else:
                    self.delete_task(message)
            elif action == "View Tasks":
                self.show_tasks()
            elif action == "Exit":
                self.logger.info(f"{username} requesting exit.")
                message = {"action": "Exit",
                           "message": "Exiting... Goodbye..."}

                self.connectionHandler.pushMessage(message)
                self.server.close_client(self.connectionHandler)

        elif self.currentState == State.AdminDashboard:
            """The main functionality of the program after authentication(login/signup)"""
            self.logger.info("State Machine Started")
            if self.currentState == State.AdminDashboard:
                self.currentState = State.AdminDashboard
                self.previousState = State.LoggingIn
                self.logger.info(f"State changed to {self.currentState}")
                if action == "Create Task":
                    if isinstance(message, dict):
                        self.logger.info(f"Creating task: {message}")
                        self.createTask(message)
                elif action == "Update Task":
                    if isinstance(message, dict):  # wont process client response of success or failed
                        self.update_task(message, username)
                elif action == "Delete Task":
                    if isinstance(message, str) and message == "Success":
                        self.logger.info("Delete task operation was successful")
                        self.show_tasks()
                    else:
                        self.delete_task(message)
                elif action == "View Tasks":
                    self.show_tasks()
                elif action == "Exit":
                    self.logger.info(f"{username} requesting exit.")
                    message = {"action": "Exit",
                               "message": "Exiting... Goodbye..."}

                    self.connectionHandler.pushMessage(message)
                    self.server.close_client(self.connectionHandler)
                elif action == "View Users":
                    self.view_users()


    def get_userID(self,username):
        return self.db.get_userID_fromDB(username)

    def createTask(self, message):
        result = self.db.insert_task(
            message["description"],
            message["due_date"],
            message["active"],
            message["assigned_to"],
            message["username"]
        )
        if result == "Success":
            message = {"action": "Create Task",
                       "message": "Task created successfully."}
            self.connectionHandler.pushMessage(message)
        else:
            message = {"action": "Create Task",
                       "message": "Failed to create task."}
            self.connectionHandler.pushMessage(message)
            self.server.notification()

    def update_task(self, message, username):
        if isinstance(message, str):
            return
        # Get the creator's user ID
        assigned_by = self.get_userID(message.get('username', username))
        if not assigned_by:
            self.logger.error(f"Creator user ID not found for {username}")
            response = {"action": "Update Task", "message": "Failed"}
            self.connectionHandler.pushMessage(response)
            return

        result = self.db.update_task(
            message["TaskID"],
            message["description"],
            message["due_date"],
            message["active"],
            message["assigned_to"],
            assigned_by
        )

        self.connectionHandler.pushMessage({
            "action": "Update Task",
            "message": "Success" if result == "Success" else "Failed"
        })
        self.server.notification()

    def delete_task(self, message):
        task_id = message["task_id"]
        if self.db.delete_task(task_id) == "Success":
            self.logger.info(f"Task {task_id} deleted")
            response = {
                "action": "Delete Task",
                "message": "Success"
            }
            self.connectionHandler.pushMessage(response)
        else:
            response = {
                "action": "Delete Task",
                "message": "Failed"
            }
            self.connectionHandler.pushMessage(response)
            self.server.notification()

    def show_tasks(self):
        tasks_str = self.db.show_tasks()
        try:
            if not tasks_str:
                self.logger.info("No tasks found in database")
                response = {
                    "action": "View Tasks",
                    "message": "No tasks available."
                }
            else:
                self.logger.info(f"Found tasks, sending to client")
                response = {
                    "action": "View Tasks",
                    "message": tasks_str
                }

            self.connectionHandler.pushMessage(response)

        except Exception as e:
            self.logger.error(f"Error in show_tasks: {e}")
            response = {
                "action": "View Tasks",
                "message": "Error retrieving tasks."
            }
            self.connectionHandler.pushMessage(response)


    def view_users(self):
        result = self.db.show_users()
        message = {"action": "View users",
                  "message": result}
        self.connectionHandler.pushMessage(message)


    """
    # This implementation expected the client to send CSV, however i changed the the way of communication to JSON

    def createTask(self, message,username):
        seperated_message = [item.strip() for item in message.split(",")]
        created_by = self.get_userID(username)
        assigned_to = self.get_userID(seperated_message[3])
        self.db.insert_task(seperated_message[0],seperated_message[1],seperated_message[2],assigned_to)

    #  message will be (task_description, due_date, active, assigned_to, created_by/updated_by, TaskID
    def update_task(self,message,username):
        seperated_message = [item.strip() for item in message.split(",")]
        updated_by = self.get_userID(username)
        assigned_to = self.get_userID(seperated_message[3])
        self.db.update_task(seperated_message[0],seperated_message[1],seperated_message[2],assigned_to,seperated_message[4])

    """

