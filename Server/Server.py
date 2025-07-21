"""The server file initializes a listen thread and listens for new connections. It initiates each connection's connectionhandler
and state machine. It also exchanges RSA public keys with the clients and then generates and sends them, rsa encrypted AES keys.
The communication encryption then switches to AES. In addition, when a new message has come, the buffer sends a notification
to the server and the server forwards the message to the state machine. Tried to implement a notification system that
alerts all active users for new task updates, however pop-ups fight each other in the same computer. Maybe the problem will
go away if users sign in from different computers. In addition, there are 2 functions quit server and close client, that manage
shutdowns gracefully, closing all threads and the socket."""




import json
import socket
import ServerLogger
import threading
from ServerLib import ConnectionHandler
from StateMachine import StateMachine, State
import Encryption
from Crypto.PublicKey import RSA
import time


class Server:
    def __init__(self, ADDRESS, PORT):
        self.ADDRESS = ADDRESS
        self.PORT = PORT
        self.logger = ServerLogger.server_logger
        self.running = True
        self.state_machines = {}
        self.active_connections = {}
        self.lock = threading.Lock()
        self.listen_thread = threading.Thread(target=self.listen)
        self.state = State.Start
        self.RsaEncryption = Encryption.RsaEncryption()


    def start_listen_thread(self):
        self.logger.info("Starting listen thread.")
        self.listen_thread.start()

    # Listens for clients.
    def listen(self):
        self.logger.debug("Listening thread started")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ADDRESS, self.PORT))
            s.listen(5)
            self.logger.info(f"Server listening on {self.ADDRESS}:{self.PORT}")

            while self.running:
                try:
                    client_socket, client_address = s.accept()
                    self.logger.info(f"Accepted connection from {client_address}")



                    # RSA Key exchange protocol - The server sends its public key, it receives the client's public key,
                    # verifies if it has indeed
                    #received the whole key and validates the key.

                    # Set a timeout for the key exchange
                    client_socket.settimeout(30)

                    try:
                        # Send server's public key with length prefix
                        server_public_key = self.RsaEncryption.getPublicKey()
                        key_length = len(server_public_key)
                        length_header = str(key_length).zfill(4).encode('utf-8')

                        self.logger.info(f"Sending public key (length: {key_length})")
                        client_socket.sendall(length_header)
                        client_socket.sendall(server_public_key)

                        # Receive client's public key with length prefix
                        self.logger.info("Waiting for client's public key...")
                        length_data = client_socket.recv(4)
                        if not length_data:
                            raise ConnectionError("No key length received from client")

                        key_length = int(length_data.decode('utf-8'))
                        self.logger.info(f"Expecting client key of length: {key_length}")

                        # Receive the full key
                        client_public_key_data = b""
                        while len(client_public_key_data) < key_length:
                            remaining = key_length - len(client_public_key_data)
                            chunk = client_socket.recv(min(remaining, 2048))
                            if not chunk:
                                raise ConnectionError("Connection closed while receiving key")
                            client_public_key_data += chunk

                        self.logger.info(f"Received client's public key, length: {len(client_public_key_data)}")

                        # Validate the key- Checks if the key given is indeed a public key and not a private key or invalid data
                        try:
                            client_public_key = RSA.import_key(client_public_key_data)
                            if not client_public_key.has_private():
                                self.logger.info("Successfully validated client's public key")
                            else:
                                raise ValueError("Received key is not a public key")
                        except (ValueError, TypeError) as e:
                            raise ValueError(f"Invalid public key received: {e}")



                        # AES key exchange protocol

                        #Create an aes instanse and get the key
                        aes_encryption = Encryption.AESencryption()
                        aes_key = aes_encryption.get_key()


                        #encrypt the key using rsa
                        encryptedAESkey = self.RsaEncryption.encrypt(aes_key,client_public_key)


                        #Send the key to the client with the length and header
                        key_length = len(encryptedAESkey)
                        length_header = str(key_length).zfill(4).encode('utf-8')
                        self.logger.debug(f"Sending encrypted AES key (length: {key_length})")
                        client_socket.sendall(length_header)
                        client_socket.sendall(encryptedAESkey.encode('utf-8'))


                        # Create connection handler and state machine
                        connection = ConnectionHandler(client_socket, client_address, client_public_key,self.RsaEncryption,aes_encryption)



                        state_machine = StateMachine(connection, client_public_key, self)
                        connection.set_state_machine(state_machine)

                        with self.lock:
                            self.active_connections[connection] = state_machine
                            self.state_machines[connection] = state_machine

                        # Set up message handling and start the connection
                        connection.on_message_ready = lambda conn=connection: self.process_message(conn)
                        connection.start()

                    except Exception as e:
                        self.logger.error(f"Key exchange failed: {e}")
                        client_socket.close()
                        continue

                except socket.error as e:
                    self.logger.error(f"Socket accept error: {e}")
                    continue

    def process_message(self, connection):
        """Sends the message to state machine for processing."""
        try:
            if connection in self.active_connections:
                self.logger.debug("Getting message from connection...")
                message = connection.getMessage()

                if message:
                    self.logger.debug(f"Processing message: {message}")
                    try:
                        state_machine = self.active_connections[connection]
                        self.logger.debug("Calling state machine handle_action...")
                        state_machine.handle_action(message)
                        self.logger.debug("State machine handle_action completed")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error. Invalid Json: {e}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.close_client(connection)


    def close_client(self, connection):
        """Closes the client"""
        try:
            with self.lock:
                if connection in self.active_connections:
                    connection.stop_threads_on_exit()
                    del self.state_machines[connection]
                    del self.active_connections[connection]
                    self.logger.info(f"Client {connection.address} disconnected.")
        except Exception as e:
            self.logger.error(f"Error during client closing connection: {e}")


    # A method to shut down the server gracefully closing each connection and the associated threads.
    def quit_server(self):
        """A method to shut down the server gracefully closing each connection and the associated threads."""
        self.running = False
        self.logger.info("Server is shutting down...")
        with self.lock:
            for connection in list(self.state_machines.keys()):
                self.close_client(connection) # called the function to gracefully stop each connection
            self.active_connections.clear()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ADDRESS, self.PORT))
        except:
            pass
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join()
        self.logger.info("Server shutdown complete...")

    def notification(self):
        with self.lock:
            for connection in self.active_connections:
                    try:
                        message = {"action":"notification",
                                   "message":"A task has been created or modified"}
                        connection.pushMessage(message)
                    except Exception as e:
                        self.logger.error(f"Error during notification message: {e}")



def main():
    try:
        server = Server("127.0.0.1", 8080)
        server.start_listen_thread()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.quit_server()

    except Exception as e:
        print(f"Server error: {e}")


if __name__ == "__main__":
    main()
"""
if __name__ == "__main__":
    server = Server(ADDRESS="127.0.0.1", PORT=8080)
    server.start_listen_thread()
"""