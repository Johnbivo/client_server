"""This file contains all UI elements and some functionality to trigger events and get user entry information
and send it to the server. Every window is a different function. There is a login fucntion UI, a signup function UI,
a Dashboard function UI where users can Create, Update, Read, Delete (CRUD) tasks.

All users have a welcome message greeting them with their name, 2 buttons createTask and refresh.
!!!Admins have an extra button called view users!!!
Below these, all tasks are shown with titles.
In addition, every task is shown dynamically, meaning that if there are 3 tasks, only 3 widgets will be created.
Each widget has an edit and a delete button.

Create and edit task open a seperate window (popups) where the user/admin can fill information in the entry points and
submit it. The corrisponding functions then pack the message into a dict format that the server will understand
and pushes the message to the buffer to be sent to the server.
"""



import customtkinter as ctk
import ClientEncryption
import ClientLogger
from customtkinter import CTkScrollableFrame
from ClientStateMachine import State


class ClientUI(ctk.CTk):
    def __init__(self, client):
        super().__init__()
        self.geometry("600x400")
        self.title("Task Manager Client")
        self.client = client
        ctk.set_appearance_mode("dark")
        self.caesar_encryption = ClientEncryption.CaesarCipher()
        self.hash_encryption = ClientEncryption.HashEncryption()
        self.logger = ClientLogger.client_logger

    def create_login_ui(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="Log In", font=("Arial", 24, "bold")).pack(pady=20)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        ctk.CTkButton(self, text="Log In", font=("Arial", 20, "bold",), command=self.handle_login, fg_color="green",
                      text_color="black").pack(pady=10)
        ctk.CTkButton(self, text="Sign Up", font=("Arial", 15), command=self.create_signup_ui, fg_color="light blue",
                      text_color="black").pack(pady=10)

    def create_signup_ui(self):
        self.clear_ui()
        ctk.CTkLabel(self, text="Sign up", font=("Arial", 24, "bold")).pack(pady=20)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        ctk.CTkButton(self, text="Back to login area", command=self.create_login_ui).pack(pady=10)
        ctk.CTkButton(self, text="Create Account", command=self.handle_signup, fg_color="green").pack(pady=10)

    def create_dashboard_ui(self, username):
        """Creates the dashboard of the task manager"""
        self.clear_ui()
        self.geometry("800x600")
        self.title("Task Manager Dashboard")


        #Created frames to group elements together and place them according to their corresponding frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True)

        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=10, pady=5)

        # Added the username to create a small greeting message with the user's name.
        ctk.CTkLabel(header_frame, text=f"Welcome {username} 😊", font=("Arial", 24, "bold")).pack(side="left", padx=10)

        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=10)

        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        headers_frame = ctk.CTkFrame(content_frame)
        headers_frame.pack(fill="x", padx=5, pady=5)


        # Creating the header labels in the header frame
        ctk.CTkLabel(headers_frame, text="ID", width=50, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Description", width=200, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Assigned To", width=100, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Due Date", width=100, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Status", width=70, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Actions", width=150, font=("Arial", 12, "bold")).pack(side="left", padx=5)

        # Create a frame where the user can scroll
        self.tasks_frame = CTkScrollableFrame(content_frame)
        self.tasks_frame.pack(fill="both", expand=True, padx=5, pady=5)



        # Create the buttons in the button frame - When pressed, will trigger the function in command
        ctk.CTkButton(button_frame, text="New Task", command=self.show_create_task_popup).pack(side="left", padx=5)
        self.refresh_button = ctk.CTkButton(button_frame, text="Refresh", command=self.handle_refresh)
        self.refresh_button.pack(side="left", padx=5)

        # Add the extra button for the admin account
        if self.client.state_machine.currentState == State.AdminDashboard:
            ctk.CTkButton(button_frame, text="View Users", command=self.view_users_popup).pack(side="left", padx=5)


        # Load the tasks the first time
        self.handle_refresh()

    def display_tasks(self, tasks):
        """Display tasks closing existing ones"""
        try:
            # Schedule UI updates using after() to avoid widget conflicts
            def safe_clear_widgets():
                try:
                    for widget in self.tasks_frame.winfo_children():
                        try:
                            widget.destroy()
                        except Exception:
                            pass
                    self.tasks_frame.update()
                    display_new_tasks()
                except Exception as e:
                    self.logger.error(f"Error clearing widgets: {e}")

            def display_new_tasks():
                try:

                    # Reset the button
                    if self.refresh_button:
                        self.refresh_button.configure(text="Refresh", state="normal")

                    # Destroy the loading_label
                    if self.loading_label:
                        try:
                            self.loading_label.destroy()
                        except Exception:
                            self.logger.error("Error destroying loading label")

                    if not tasks:
                        ctk.CTkLabel(self.tasks_frame,text="No tasks available",font=("Arial", 12)).pack(pady=20)
                        return

                    # Display tasks dynamically with edit and delete buttons
                    for task in tasks:
                        try:
                            task_frame = ctk.CTkFrame(self.tasks_frame)
                            task_frame.pack(fill="x", padx=5, pady=2)

                            # Create the task labels
                            ctk.CTkLabel(task_frame, text=str(task["TaskID"]), width=50).pack(side="left", padx=5)
                            ctk.CTkLabel(task_frame, text=task["Description"], width=200).pack(side="left", padx=5)
                            ctk.CTkLabel(task_frame, text=str(task["assigned_to"]), width=100).pack(side="left", padx=5)
                            ctk.CTkLabel(task_frame, text=task["due_date"], width=100).pack(side="left", padx=5)

                            # Set the color of active based on active/Inactive
                            if task["active"] == "1":
                                active_status = "Active"
                            else:
                                active_status = "Inactive"
                            if task["active"] == "1":
                                status_color = "green"
                            else:
                                status_color = "red"

                            ctk.CTkLabel(task_frame,text=active_status,width=70,text_color=status_color).pack(side="left", padx=5)

                            # Create a frame for edit and delete
                            edit_delete_frame = ctk.CTkFrame(task_frame, fg_color="transparent", width=150)
                            edit_delete_frame.pack(side="left", padx=5)

                            ctk.CTkButton(edit_delete_frame, text="Edit",command=lambda t=task: self.show_edit_task_popup(t),width=60).pack(side="left", padx=2)
                            ctk.CTkButton(edit_delete_frame, text="Delete",command=lambda t=task: self.handle_delete_task(t),fg_color="red", width=60).pack(side="left", padx=2)

                        except Exception as e:
                            self.logger.error(f"Error creating task row: {e}")
                            continue

                except Exception as e:
                    self.logger.error(f"Error displaying new tasks: {e}")

            # Updating the widgets with a little time to avoid collisions.
            self.after(100, safe_clear_widgets)

        except Exception as e:
            self.logger.error(f"Error in display_tasks: {e}")

    def show_create_task_popup(self):
        """Creates a new window popup in the center of the main window dashboard"""
        popup = ctk.CTkToplevel(self)
        popup.title("Create New Task")
        popup.geometry("400x350")

        #Dashboard UI is the parent in this case
        # Get the center
        popup.transient(self)  #Become associated with dashboard. Stays on top of dashboard no matter what
        popup.grab_set() # Stops the functionality of the dashboard until the window closes

        # Centers the dialog popup relative to dashboard
        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2) #Horizontal
        y = self.winfo_y() + (self.winfo_height() // 2) - (350 // 2) #Vertical
        popup.geometry(f"+{x}+{y}") # Places the popup using the coordinates taken by x and y


        #self.winfo_x() and self.winfo_x() get the coordinated of top-left corner of dashboard
        #self.winfo_width() and self.winfo_height() get the width and height of dashboard

        # Create the popup's elements
        ctk.CTkLabel(popup, text="Create New Task", font=("Arial", 16, "bold")).pack(pady=10)

        description_entry = ctk.CTkEntry(popup, placeholder_text="Description")
        description_entry.pack(pady=5)

        assigned_to_entry = ctk.CTkEntry(popup, placeholder_text="Assigned To (username)")
        assigned_to_entry.pack(pady=5)

        due_date_entry = ctk.CTkEntry(popup, placeholder_text="Due Date (YYYY-MM-DD)")
        due_date_entry.pack(pady=5)

        active_var = ctk.BooleanVar(value=True) # Set the default to Active(true) for the checkbox
        active_checkbox = ctk.CTkCheckBox(popup, text="Active", variable=active_var)
        active_checkbox.pack(pady=10)


        #Created a nested function submit because it will be only called when the user wants to create a task
        # In addition, puts the entry points to the correct dict format that the server can receive.

        def submit():
            message = {
                "action": "Create Task",
                "message": {
                    "description": description_entry.get(),
                    "assigned_to": assigned_to_entry.get(),
                    "due_date": due_date_entry.get(),
                    "active": active_var.get(),
                    "username": self.client.state_machine.getUsername()
                }
            }
            self.client.state_machine.create_task(message)
            popup.destroy()
            self.client.state_machine.request_tasks()


        # The submit button that will trigger the function above "submit"
        ctk.CTkButton(popup, text="Create", command=submit).pack(pady=10)


    def show_edit_task_popup(self, task):
        """Will create a popup for the edit task"""

        # Same as the create task, with different functionality.

        popup = ctk.CTkToplevel(self)
        popup.title("Edit Task")
        popup.geometry("400x350")

        popup.transient(self)
        popup.grab_set()

        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (350 // 2)
        popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(popup, text=f"Edit Task {task['TaskID']}", font=("Arial", 16, "bold")).pack(pady=10)

        # I insert existing info into the entry points. The user then can modify and submit them.
        description_entry = ctk.CTkEntry(popup, placeholder_text="Description")
        description_entry.insert(0, task["Description"])
        description_entry.pack(pady=5)

        assigned_to_entry = ctk.CTkEntry(popup, placeholder_text="Assigned To")
        assigned_to_entry.insert(0, str(task["assigned_to"])) # because the database keeps user ID's (int), make it a string
        assigned_to_entry.pack(pady=5)

        due_date_entry = ctk.CTkEntry(popup, placeholder_text="Due Date (YYYY-MM-DD)")
        due_date_entry.insert(0, task["due_date"])
        due_date_entry.pack(pady=5)


        active_var = ctk.BooleanVar(value=task["active"] == "1")
        active_checkbox = ctk.CTkCheckBox(popup, text="Active", variable=active_var)
        active_checkbox.pack(pady=10)

        def submit():
            message = {
                "action": "Update Task",
                "message": {
                    "TaskID": task['TaskID'],
                    "description": description_entry.get(),
                    "assigned_to": assigned_to_entry.get(),
                    "due_date": due_date_entry.get(),
                    "active": active_var.get(),
                    "username": self.client.state_machine.getUsername()
                }
            }
            self.client.state_machine.update_task(message)
            popup.destroy()
            self.client.state_machine.request_tasks()

        ctk.CTkButton(popup, text="Save Changes", command=submit).pack(pady=10)

    def handle_delete_task(self, task):
        message = {
            "action": "Delete Task",
            "message": {"task_id": task["TaskID"]}
        }
        self.client.state_machine.delete_task(message)
        # Refresh tasks after deletion
        self.client.state_machine.request_tasks()

    def clear_ui(self):
        """Clears the UI"""
        try:
            # Cancel any pending after callbacks
            self.after_cancel("all")
            widgets = list(self.winfo_children())

            # Destroy the widgets
            for widget in widgets:
                try:
                    widget.pack_forget()
                    widget.destroy()
                except Exception as e:
                    self.logger.error(f"Error destroying widget: {e}")
                    continue
            self.update()

        except Exception as e:
            self.logger.error(f"Error in clear_ui: {e}")

    def handle_login(self):
        """Sends the entries for username and password for login to the ClientStateMachine"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            return

        message = {
            "action": "login",
            "username": username,
            "password": password
        }
        self.logger.debug(f"Login attempt for user: {username}")
        # Send message to state machine
        self.client.state_machine.handle_action(message)

    def handle_signup(self):
        """Sends the entries for username and password for signup to the ClientStateMachine"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        encrypted_username = username
        message = {"action":"signup",
                   "username": username,
                   "password": password}
        self.logger.debug(f"Signup credentials sent to server")
        self.client.state_machine.handle_action(message)

    def handle_refresh(self):
        """Refreshes the tasks showing a loading text"""
        try:
            # Show loading state
            self.refresh_button.configure(text="Refreshing...", state="disabled")

            # Clear all existing tasks first
            for widget in self.tasks_frame.winfo_children():
                widget.destroy()

            # Add loading label to tasks frame
            self.loading_label = ctk.CTkLabel(self.tasks_frame,text="Loading tasks...",font=("Arial", 12))
            self.loading_label.pack(pady=20)

            self.client.state_machine.request_tasks()

        except Exception as e:
            self.logger.error(f"Error during refresh: {e}")
            self.refresh_button.configure(text="Refresh", state="normal")
            if hasattr(self, 'loading_label'):
                self.loading_label.destroy()

    def show_notification(self, title, message, type="success"):
        """Shows a notification on the requested action will colors"""
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("300x150")
        popup.transient(self)
        popup.grab_set()

        x = self.winfo_x() + (self.winfo_width() // 2) - (300 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (150 // 2)
        popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(popup, text=message, font=("Arial", 14)).pack(pady=20)

        def close_popup():
            popup.destroy()

        ctk.CTkButton(popup,text="OK",command=close_popup,fg_color="green",text_color="white",width=100).pack(pady=10)

        if type == "success":
            self.after(2000, close_popup)

    def view_users_popup(self):
        self.users_dialog = ctk.CTkToplevel(self)
        self.users_dialog.title("User List")
        self.users_dialog.geometry("400x500")

        self.users_dialog.transient(self)
        self.users_dialog.grab_set()

        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (500 // 2)
        self.users_dialog.geometry(f"+{x}+{y}")

        header_frame = ctk.CTkFrame(self.users_dialog)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Users List", font=("Arial", 16, "bold")).pack(pady=10)

        # Create scrollable frame for users
        self.users_frame = CTkScrollableFrame(self.users_dialog)
        self.users_frame.pack(fill="both", expand=True, padx=10, pady=5)

        headers_frame = ctk.CTkFrame(self.users_frame)
        headers_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(headers_frame, text="Username", width=200, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Role", width=100, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkButton(self.users_dialog, text="Close", command=self.users_dialog.destroy, width=100).pack(pady=10)

        # Request users data from state machine
        self.client.state_machine.view_users()

    def display_users(self, users_data):
        """Displays the users...Admins only"""
        if not hasattr(self, 'users_frame'):
            return

        # Clear existing users (except headers)
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        headers_frame = ctk.CTkFrame(self.users_frame)
        headers_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(headers_frame, text="Username", width=200, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Role", width=100, font=("Arial", 12, "bold")).pack(side="left", padx=5)

        if not users_data:
            ctk.CTkLabel(self.users_frame, text="No users available", font=("Arial", 12)).pack(pady=20)
            return

        for user in users_data:
            user_frame = ctk.CTkFrame(self.users_frame)
            user_frame.pack(fill="x", padx=5, pady=2)

            ctk.CTkLabel(user_frame, text=user["username"], width=200).pack(side="left", padx=5)

            role_color = "green" if user["role"] == "admin" else "lightblue"
            ctk.CTkLabel(user_frame, text=user["role"], width=100, text_color=role_color).pack(side="left", padx=5)


