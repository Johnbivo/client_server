# Task Management System

A secure, multi-user task management application built with Python, featuring client-server architecture with end-to-end encryption, real-time notifications, and a modern GUI interface.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure login/signup system with role-based access control
- **Task Management**: Full CRUD operations (Create, Read, Update, Delete) for tasks
- **Multi-User Support**: Multiple clients can connect simultaneously
- **Role-Based Access**: Admin and User roles with different permissions
- **Real-time Updates**: Live task updates and notifications

### Security Features
- **End-to-End Encryption**: RSA key exchange followed by AES encryption
- **Secure Communication**: All client-server communication is encrypted
- **Password Hashing**: MD5 hashing for password storage
- **Key Validation**: Robust RSA key validation and exchange protocol

### User Interface
- **Modern GUI**: Built with CustomTkinter for a sleek, dark-themed interface
- **Responsive Design**: Dynamic task display with scrollable interface
- **Intuitive Navigation**: Easy-to-use buttons and forms
- **Real-time Notifications**: Pop-up alerts for task updates

## 🏗️ Architecture

### Client-Server Model
- **Server**: Centralized task management and user authentication
- **Client**: GUI-based interface for user interaction
- **Database**: SQLite database for persistent data storage

### Communication Protocol
1. **RSA Key Exchange**: Initial secure key establishment
2. **AES Encryption**: Symmetric encryption for ongoing communication
3. **State Machine**: Robust message handling and state management

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Task-Management-System
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   - Ensure all required packages are installed
   - Check that Python can import the required modules

## 🚀 Usage

### Starting the Server

1. **Navigate to the Server directory**
   ```bash
   cd Server
   ```

2. **Start the server**
   ```bash
   python Server.py
   ```

   The server will start listening on:
   - **Address**: 127.0.0.1 (localhost)
   - **Port**: 8080

### Starting the Client

1. **Open a new terminal and navigate to the Client directory**
   ```bash
   cd Client
   ```

2. **Start the client**
   ```bash
   python Client.py
   ```

3. **Multiple clients**: You can start multiple client instances for different users

### Default Accounts

#### Admin Account
- **Username**: `admin`
- **Password**: `admin`
- **Permissions**: Full access including user management

#### User Account
- **Username**: `john`
- **Password**: `john`
- **Permissions**: Task management only

### Creating New Accounts

1. **User Accounts**: Can be created through the client interface
2. **Admin Accounts**: Must be created through the database (see Database.py)

## 📁 Project Structure

```
Task-Management-System/
├── Server/
│   ├── Server.py              # Main server application
│   ├── Database.py            # Database operations and schema
│   ├── Encryption.py          # Encryption/decryption utilities
│   ├── Authentication.py      # User authentication logic
│   ├── StateMachine.py        # Server state management
│   ├── ServerLib.py           # Server utilities and helpers
│   ├── ServerLogger.py        # Logging configuration
│   ├── task_manager.db        # SQLite database file
│   └── server_log.log         # Server activity logs
├── Client/
│   ├── Client.py              # Main client application
│   ├── GUI.py                 # User interface implementation
│   ├── ClientStateMachine.py  # Client state management
│   ├── ClientLib.py           # Client utilities and helpers
│   ├── ClientEncryption.py    # Client-side encryption
│   ├── ClientLogger.py        # Client logging configuration
│   └── client_log.log         # Client activity logs
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── readme.txt                 # Basic usage instructions
```

## 🔧 Technical Details

### Database Schema

#### Users Table
- `UserID` (Primary Key)
- `Username` (Unique)
- `Password` (Hashed)
- `Role` (admin/user)
- `AccountCreatedAt` (Timestamp)

#### Tasks Table
- `TaskID` (Primary Key)
- `TaskDescription`
- `DateOfCreation`
- `DueDate`
- `Active` (Boolean)
- `Created_by` (Foreign Key to Users)
- `Assigned_to` (Foreign Key to Users)

### Encryption Implementation

1. **RSA Encryption**: 2048-bit key generation for secure key exchange
2. **AES Encryption**: 256-bit symmetric encryption for message security
3. **Hash Encryption**: MD5 hashing for password storage
4. **Caesar Cipher**: Legacy encryption method (kept for development history)

### State Machine

The application uses state machines for both client and server to manage:
- Connection states
- Authentication states
- Task operation states
- Error handling states

## 🔒 Security Features

- **Secure Key Exchange**: RSA-based public key exchange
- **Message Encryption**: AES-GCM for authenticated encryption
- **Password Security**: MD5 hashing for password storage
- **Connection Validation**: Robust key validation and error handling
- **Thread Safety**: Locked database operations for concurrent access

## 📝 Logging

Both client and server maintain detailed logs:
- **Server Logs**: Connection events, authentication, database operations
- **Client Logs**: Connection status, GUI events, encryption operations
- **Log Levels**: Debug, Info, Warning, Error

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Ensure no other application is using port 8080
   - Check if server is already running

2. **Connection Refused**
   - Verify server is running before starting client
   - Check firewall settings

3. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify Python version compatibility

4. **Database Errors**
   - Check file permissions for `task_manager.db`
   - Ensure SQLite is properly installed

### Debug Mode

Enable detailed logging by modifying the logger configuration in:
- `Server/ServerLogger.py`
- `Client/ClientLogger.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is developed for educational purposes.

## 👨‍💻 Author

**Ioannis Bivolaris**

