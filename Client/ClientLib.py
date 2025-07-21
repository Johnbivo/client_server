"""
same as the server's Serverlib



This file handles incoming and outgoing messages, encrypts and decrypts them automatically using AES encryption
Incoming messages are put into a buffer which then check if all the message came. Then it alerts the server that a message
has been received and put into the buffer. When the server tries to get the message from the buffer, the message gets decrypted
automatically and sent.


Outgoing messages are put into a buffer too and are automatically encrypted before sending them to client.

2 threads are initialized for each connection. One to manage sending messages and one to receive external messages.
There are 2 main functions read and write...Each function has its own thread

The write function sends messages that are queued in the oBuffer
The read function receives external messages from the clients and puts them into the iBuffer after verifying
the message came whole and notifies the server.


"""





import ClientLogger
import threading
import queue
import socket
import json
import time
import errno
import ClientEncryption
import binascii

# Same class as the server's ConnectionHandler. The client will have a read and write threads too to allow seamless communication with minimal delay.
class ConnectionHandler:
    def __init__(self, server_socket, server_address, server_public_key=None, RsaEncryption=None, aes_key=None):
        self.socket = server_socket
        self.address = server_address
        self.server_public_key = server_public_key
        self.logger = ClientLogger.client_logger
        self.lock = threading.Lock()

        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

        self.packetHeaderLength = 4
        self.networkBuffer = ""
        self.messageBuffer = ""
        self.messageInProgress = False
        self.messageBytesRemaining = 0

        self.running = True
        self.writing = True
        self.reading = True

        self.on_message_ready = lambda: None

        self.readThread = threading.Thread(target=self.read, daemon=True)
        self.writeThread = threading.Thread(target=self.write, daemon=True)

        self.RsaEncryption = RsaEncryption
        self.caesarCipher = ClientEncryption.CaesarCipher()
        self.hashEncryption = ClientEncryption.HashEncryption()
        self.AesEncryption = ClientEncryption.AESencryption()
        if aes_key:
            self.AesEncryption.set_key(aes_key)

        self.state_machine = None

    def set_state_machine(self, state_machine):
        """Set the state machine after initialization"""
        self.state_machine = state_machine

    def write(self):
        try:
            while self.writing:
                if not self.running and self.oBuffer.empty():
                    self.writing = False
                    self.logger.error("Write thread stopped")
                if not self.oBuffer.empty():
                    try:
                        with self.lock:
                            message = self.oBuffer.get()

                            # Determine if the message is bytes or string
                            if isinstance(message, str):
                                message = message.encode("utf-8")

                            messageLength = str(len(message)).zfill(self.packetHeaderLength).encode("utf-8")
                            self.socket.sendall(messageLength + message)

                    except Exception as e:
                        self.logger.error(f"Write error: {str(e)}")
                        self.writing = False
                time.sleep(0.1) # Added this to prevent cpu spinning (continously checking for a message in the obuffer)

        except Exception as e:
            self.logger.error(f"Write thread error: {str(e)}")
        finally:
            self.logger.info("Write thread finished")

    def read(self):
        try:
            with self.socket:
                self.socket.setblocking(False)
                self.logger.info(f"Connection established with server at {self.address}")

                while self.reading:
                    if not self.running:
                        self.reading = False
                        self.stop_threads_on_exit()
                        break
                    try:
                        data = self.socket.recv(1024)

                        if data:
                            message = data.decode("utf-8")
                            self.networkBuffer += message
                            self.logger.debug(f"Received data from server: {message}")

                            while len(self.networkBuffer) > 0:
                                if not self.messageInProgress:
                                    if len(self.networkBuffer) >= self.packetHeaderLength:
                                        self.messageBytesRemaining = int(self.networkBuffer[:self.packetHeaderLength])
                                        self.networkBuffer = self.networkBuffer[self.packetHeaderLength:]
                                        self.messageInProgress = True
                                    else:
                                        break

                                if self.messageInProgress:
                                    if len(self.networkBuffer) >= self.messageBytesRemaining:
                                        message_content = self.networkBuffer[:self.messageBytesRemaining]
                                        self.networkBuffer = self.networkBuffer[self.messageBytesRemaining:]

                                        with self.lock:
                                            self.iBuffer.put(message_content)
                                            self.logger.debug(f"Message added to input buffer: {message_content}")

                                        self.messageInProgress = False
                                        self.messageBytesRemaining = 0

                                        self.on_message_ready()
                                    else:
                                        break

                        elif data == b'':
                            if self.running:
                                self.logger.info("Server disconnected")
                                self.running = False

                            break

                    except OSError as e:
                        err = e.args[0]
                        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                            time.sleep(0.1)
                        else:
                            self.logger.error(f"Socket error: {e}")
                            self.running = False
                            try:
                                self.socket.shutdown(socket.SHUT_RDWR)
                            except OSError as e:
                                if e.errno == 10038:
                                    self.logger.error("Socket already closed")
                            finally:
                                self.socket.close()
                            break

        except Exception as e:
            self.logger.error(f"Read thread error: {str(e)}")
        finally:
            self.logger.info("Read thread finished")

    def stop_threads_on_exit(self):
        self.logger.info("Stopping connection handler threads")

        self.running = False
        self.reading = False
        self.writing = False

        try:
            if hasattr(self, 'socket') and not self.socket._closed:
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except (OSError, socket.error):
                    pass
                try:
                    self.socket.close()
                except (OSError, socket.error):
                    pass

            if hasattr(self, 'readThread'):
                self.readThread.join(timeout=2.0)
                if self.readThread.is_alive():
                    self.logger.warning("Read thread did not terminate cleanly")

            if hasattr(self, 'writeThread'):
                self.writeThread.join(timeout=2.0)
                if self.writeThread.is_alive():
                    self.logger.warning("Write thread did not terminate cleanly")

        except Exception as e:
            self.logger.error(f"Error during thread cleanup: {str(e)}")
        finally:
            self.logger.info("Connection handler terminated")

    def start(self):
        self.logger.info("Starting connection handler threads")
        self.readThread.start()
        self.writeThread.start()

    def pushMessage(self, message_dict):
        try:
            if "password" in message_dict.keys():
                message_dict["password"] = self.hashEncryption.encrypt_password(message_dict["password"])
            message = json.dumps(message_dict)
            encrypted_data = self.AesEncryption.encrypt_text(message)
            message_to_send = {
                'ciphertext': binascii.hexlify(encrypted_data[0]).decode('utf-8'),
                'aesIV': binascii.hexlify(encrypted_data[1]).decode('utf-8'),
                'authTag': binascii.hexlify(encrypted_data[2]).decode('utf-8')
            }
            self.oBuffer.put(json.dumps(message_to_send))
            self.logger.info("Message encrypted and queued for sending")

        except Exception as e:
            self.logger.error(f"Error encrypting message: {e}")
            raise

    def getMessage(self):
        if not self.iBuffer.empty():
            try:
                message = self.iBuffer.get()
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                encrypted_dict = json.loads(message)

                # Convert from hex strings back to bytes
                encrypted_data = (
                    binascii.unhexlify(encrypted_dict['ciphertext']),
                    binascii.unhexlify(encrypted_dict['aesIV']),
                    binascii.unhexlify(encrypted_dict['authTag'])
                )

                decrypted_message = self.AesEncryption.decrypt_text(encrypted_data)
                return json.loads(decrypted_message)

            except Exception as e:
                self.logger.error(f"Error decrypting message: {e}")
                raise

        return None



