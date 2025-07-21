"""
The client state machine communicates with the StateMachine of the server. Both state machines expect
standard way of message in a dictionary using keys action,message,username,password.



The ClientStateMachine handles login, signup, the GUI and the dashboard CRUD operations

Has dedicated functions for each operation...These functions send data, gotten from the GUI, to the ClientLib
and all the way to the server's StateMachine.
"""




from enum import Enum
import ClientLogger
import ClientEncryption

class State(Enum):
    Start = 1
    LoggingIn = 2
    Authentication = 3
    Dashboard = 4
    AdminDashboard = 5
    Exit = 6




class ClientStateMachine:
    def __init__(self,connectionHandler,server_public_key, client,gui):
        self.currentState = State.Start
        self.previousState = None
        self.logger = ClientLogger.client_logger

        self.tasks = []


        self.connectionHandler = connectionHandler
        self.server_public_key = server_public_key
        self.client = client
        self.username = None
        self.gui = gui

        self.rsaEncryption = ClientEncryption.RsaEncryption()
        self.md5Encryption = ClientEncryption.HashEncryption()
        self.caesarCipher = ClientEncryption.CaesarCipher()

    def handle_action(self, message):
        """Handles actions"""
        self.logger.debug(f"Handling action: {message}")
        if 'action' not in message:
            self.logger.error("No action in message")
            return
        action = message['action']
        try:
            if self.currentState == State.Start:
                self.handle_start(action, message)
            elif self.currentState == State.Authentication:
                self.handle_authentication(action, message)
            elif self.currentState == State.Dashboard or self.currentState == State.AdminDashboard:
                self.handle_dashboard(action, message)
        except Exception as e:
            self.logger.error(f"Error in handle_action: {e}")


    def handle_start(self,action, message):
        if action == "login":
            self.currentState = State.Authentication
            self.previousState = State.Start
            if 'username' in message:
                self.username = message['username']
            self.connectionHandler.pushMessage(message)
            self.logger.debug("Login message sent to server")
        elif action == "signup":
            self.currentState = State.Start
            self.connectionHandler.pushMessage(message)
            self.logger.debug("Signup message sent to server")



    def handle_authentication(self,action, message):
        if "message" in message:
            if message["message"] == "Provide Access":
                self.currentState = State.Dashboard
                self.logger.info(f"Access granted for user: {self.username}")
                self.gui.create_dashboard_ui(self.username)
            elif message["message"] == "Provide Admin Access":
                self.currentState = State.AdminDashboard
                self.logger.info(f"Admin access granted for user: {self.username}")
                self.gui.create_dashboard_ui(self.username)
            elif message["message"] == "Failed":
                self.currentState = State.Start
                self.username = None
                self.logger.warning("Authentication failed")

    def handle_dashboard(self, action, message):
        if action == "Create Task":
            if message.get("message") == "Task created successfully.":
                self.gui.show_notification("Success", "Task created successfully!")
                self.request_tasks()
            else:
                self.create_task(message)

        elif action == "Update Task":
            if message.get("message") == "Success":
                self.gui.show_notification("Success", "Task updated successfully!")
                self.request_tasks()
            else:
                self.update_task(message)



        elif action == "Delete Task":
            if message.get("message") == "Success":
                self.gui.show_notification("Success", "Task deleted successfully!")
                self.request_tasks()
            else:
                self.delete_task(message)
        elif action == "View Tasks":
            self.show_tasks(message)
        elif action == "Notification":
            self.handle_notification(message)
        elif action == "Exit":
            self.logger.info(f"{self.client.ADDRESS} requesting exit.")
            message = {
                "action": "Exit",
                "message": "Exiting... Goodbye..."
            }
            self.connectionHandler.pushMessage(message)
            self.client.close_client(self.connectionHandler)



    def handle_dashboard(self, action, message):
        if action == "Create Task":
            if message.get("message") == "Task created successfully.":
                self.gui.show_notification("Success", "Task created successfully!")
                self.request_tasks()
            else:
                self.create_task(message)

        elif action == "Update Task":
            if message.get("message") == "Success":
                self.gui.show_notification("Success", "Task updated successfully!")
                self.request_tasks()
            else:
                self.update_task(message)

        elif action == "Delete Task":
            if message.get("message") == "Success":
                self.gui.show_notification("Success", "Task deleted successfully!")
                self.request_tasks()
            else:
                self.delete_task(message)
        elif action == "View Tasks":
            self.show_tasks(message)
        elif action == "Notification":
            self.handle_notification(message)
        elif action == "Exit":
            self.logger.info(f"{self.client.ADDRESS} requesting exit.")
            message = {
                "action": "Exit",
                "message": "Exiting... Goodbye..."
            }
            self.connectionHandler.pushMessage(message)
            self.client.close_client(self.connectionHandler)
        elif action == "View users":
            users_data = message.get("message", [])
            self.gui.display_users(users_data)


    def getUsername(self):
        return self.username


    def create_task(self, task):
        if self.currentState == State.Dashboard or self.currentState == State.AdminDashboard:
            self.logger.debug("Creating task")
            self.connectionHandler.pushMessage(task)

    def show_tasks(self, message):
        """Handles task display response from server"""
        try:
            if message.get("message") == "No tasks available.":
                self.tasks = []
                self.gui.display_tasks(self.tasks)
                return

            # Convert string representation to list if needed
            task_data = message.get("message")
            if isinstance(task_data, str):
                import ast
                self.tasks = ast.literal_eval(task_data)
            elif isinstance(task_data, list):
                self.tasks = task_data
            else:
                self.logger.error(f"Unexpected task data type: {type(task_data)}")
                return

            self.gui.display_tasks(self.tasks)

        except Exception as e:
            self.logger.error(f"Error showing tasks: {e}")
            self.logger.error(f"Message content: {message}")

    def request_tasks(self):
        """Send request to server for tasks"""
        try:
            message = {
                "action": "View Tasks",
                "username": self.getUsername()
            }
            self.logger.debug(f"Requesting tasks with message: {message}")
            self.connectionHandler.pushMessage(message)
        except Exception as e:
            self.logger.error(f"Error requesting tasks: {e}")

    def update_task(self, message):
        """Handles task update request"""
        try:
            self.logger.debug(f"Sending update task request: {message}")
            self.connectionHandler.pushMessage(message)
            self.logger.debug("Update task request sent")
        except Exception as e:
            self.logger.error(f"Error updating task: {e}")


    def delete_task(self,message):
        self.connectionHandler.pushMessage(message)

    def handle_notification(self, message):
        text = message.get("message", "")
        self.gui.show_notification("Notification", text)
        self.request_tasks()

    def view_users(self):
        message = {
            "action": "View Users",
            "username": self.getUsername()
        }
        self.logger.debug(f"Requesting users list")
        self.connectionHandler.pushMessage(message)



