"""The client as with the server.py, is responsible for making the connection to the server,
it establishes a connection and then exchanges RSA keys. Then the server sends the AES key encrypted,
Then the communication between the server and the client is enctypted with AES. In addition, it initialiazes
a connectionhandler in clientLib and a gui in GUI and passes incoming messages to the client state machine."""
import socket
import threading
import ClientLogger
import ClientEncryption
from ClientLib import ConnectionHandler
import GUI
from ClientStateMachine import ClientStateMachine
import json


class Client:
    def __init__(self, ADDRESS, PORT):
        self.ADDRESS = ADDRESS
        self.PORT = PORT
        self.logger = ClientLogger.client_logger
        self.lock = threading.Lock()
        self.RsaEncryption = ClientEncryption.RsaEncryption()
        self.running = True
        self.connection_handler = None
        self.state_machine = None
        self.server_socket = None


        self.gui = GUI.ClientUI(self)
        self.gui.protocol("WM_DELETE_WINDOW", self.quit_client) #If the client presses the X in the window, it triggers the quit_client function to shut the client gracefully

    def start(self):
        """Start the client"""
        self.gui.create_login_ui()
        self.server_thread = threading.Thread(target=self.connect_to_server)
        self.server_thread.daemon = True
        self.server_thread.start()

        try:
            self.gui.mainloop()
        except Exception as e:
            self.logger.error(f"GUI error: {e}")
            self.quit_client()

    def connect_to_server(self):
        """Connect to server and handle key exchange"""
        try:
            # Create socket and connect
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((self.ADDRESS, self.PORT))
            self.logger.info(f"Connected to server at {self.ADDRESS}:{self.PORT}")

            # Key exchange
            try:
                #RSA KEY EXHCHANGE PROTOCOL


                #Send the public key with length and header
                client_public_key = self.RsaEncryption.getPublicKey()
                key_length = len(client_public_key)
                length_header = str(key_length).zfill(4).encode('utf-8')

                server_socket.sendall(length_header)
                server_socket.sendall(client_public_key)
                self.logger.debug("Sent client public key")

                # Receive server's public key
                length_data = server_socket.recv(4)
                if not length_data:
                    raise ConnectionError("No key length received from server")

                key_length = int(length_data.decode('utf-8'))

                server_public_key = b""
                while len(server_public_key) < key_length:
                    remaining = key_length - len(server_public_key)
                    chunk = server_socket.recv(min(remaining, 2048))
                    if not chunk:
                        raise ConnectionError("Connection closed while receiving key")
                    server_public_key += chunk

                #AES key receive protocol


                #Receive the key length of the data first
                length = server_socket.recv(4)
                if not length:
                    raise ConnectionError("Connection closed while receiving key")

                aes_key_length = int(length.decode('utf-8'))
                self.logger.debug(f"AES key length: {aes_key_length}")
                encrypted_aes_key = b""

                # Receive the aes key and check if all of it arrived
                while len(encrypted_aes_key) < aes_key_length:
                    remaining = aes_key_length - len(encrypted_aes_key)
                    chunk1 = server_socket.recv(min(remaining, 2048))
                    if not chunk1:
                        raise ConnectionError("Connection closed while receiving AES key")
                    encrypted_aes_key += chunk1

                #Decrypt the key using RSA
                encrypted_key_string = encrypted_aes_key.decode('utf-8')
                decrypted_aes_key = self.RsaEncryption.decrypt(encrypted_key_string)


                self.connection = ConnectionHandler(server_socket, self.ADDRESS, server_public_key, self.RsaEncryption, decrypted_aes_key)
                self.state_machine = ClientStateMachine(self.connection, server_public_key, self,self.gui)
                self.connection.set_state_machine(self.state_machine)
                # Set up message handling and start the connection
                self.connection.on_message_ready = lambda conn=self.connection: self.process_message(conn)
                self.connection.start()

            except Exception as e:
                self.logger.error(f"Key exchange error: {e}")
                server_socket.close()
                return

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return

    def process_message(self, connection):
        try:
            message = connection.getMessage()
            if message:
                self.logger.debug(f"Processing message: {message}")
                try:
                    self.logger.debug("Calling state machine handle_action...")
                    self.state_machine.handle_action(message)
                    self.logger.debug("State machine handle_action completed")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error. Invalid Json: {e}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.quit_client()

    def quit_client(self):
        """Gracefully shut down the client"""
        if not self.running:
            return

        self.running = False
        self.logger.info("Client is shutting down...")

        if self.connection:
            try:
                # Send disconnect message through existing connection
                self.connection.pushMessage({
                    "action": "disconnect",
                    "message": "Client shutting down"
                })
            except Exception as e:
                self.logger.error(f"Error sending disconnect message: {e}")

        if self.connection:
            self.connection.stop_threads_on_exit()

        if hasattr(self, 'server_thread'):
            self.server_thread.join(timeout=2.0)

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")

        self.gui.quit()
        self.logger.info("Client shutdown complete")





if __name__ == "__main__":
    client = Client(ADDRESS="127.0.0.1", PORT=8080)
    client.start()