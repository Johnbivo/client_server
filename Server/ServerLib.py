"""This file handles incoming and outgoing messages, encrypts and decrypts them automatically using AES encryption
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
import errno
import queue
import threading
from socket import socket
import time
import socket
import json
import binascii
import Encryption
import ServerLogger


class ConnectionHandler:
    def __init__(self, client_socket, address, client_public_key=None,rsa_encryption = None, aes_encryption = None):
        self.client_socket = client_socket
        self.address = address
        self.client_public_key = client_public_key
        self.logger = ServerLogger.server_logger
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

        self.RsaEncryption = rsa_encryption
        self.caesarCipher = Encryption.CaesarCipher()
        self.AesEncryption = aes_encryption


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
                                message = message.encode("utf-8")  # Convert string to bytes

                            messageLength = str(len(message)).zfill(self.packetHeaderLength).encode("utf-8")
                            self.client_socket.sendall(messageLength + message)

                    except:
                        self.logger.error("Write thread stopped. Network error")
                else:
                    time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Write thread error: {str(e)}")
        finally:
            self.logger.info("Write thread finished")

    def read(self):
        try:
            with self.client_socket:
                self.client_socket.setblocking(False)
                self.logger.info("Connection established by {client}".format(client=self.client_socket.getpeername()))

                while self.reading:
                    if not self.running:
                        self.reading = False
                        self.stop_threads_on_exit()
                        break
                    try:
                        data = self.client_socket.recv(1024)

                        if data:
                            message = data.decode("utf-8")
                            self.networkBuffer += message
                            self.logger.info("Network buffer received {data} from {client}".format(client=self.client_socket.getpeername(), data=data))

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
                                        # Extract the message
                                        message_content = self.networkBuffer[:self.messageBytesRemaining]
                                        self.networkBuffer = self.networkBuffer[self.messageBytesRemaining:]

                                        with self.lock:
                                            self.iBuffer.put(message_content)
                                            self.logger.info(f"Message added to iBuffer: {message_content}")

                                        self.messageInProgress = False
                                        self.messageBytesRemaining = 0

                                        # Call state machine
                                        self.logger.info("A new message has been added to the iBuffer")
                                        self.on_message_ready()
                                    else:
                                        break

                        elif data == b'':
                            self.logger.info(f"Client {self.client_socket.getpeername()} disconnected.")
                            self.running = False
                            self.stop_threads_on_exit()
                            break

                    except OSError as e:
                        err = e.args[0]
                        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                            time.sleep(0.1)
                        else:
                            self.logger.critical(f"Socket error: {e}")
                            self.running = False
                            try:
                                self.client_socket.shutdown(socket.SHUT_RDWR)
                            except OSError as e:
                                if e.errno == 10038:
                                    self.logger.error("Socket already closed..")
                            finally:
                                self.client_socket.close()

        except Exception as e:
            self.logger.critical("Unhandled exception in read thread: {e}".format(e=e))
        finally:
            self.logger.info("Read thread finished")

    def stop_threads_on_exit(self):
        """Gracefully stop the connection threads"""
        self.logger.info("Stopping threads")

        self.running = False
        self.reading = False
        self.writing = False

        try:
            if hasattr(self, 'client_socket') and not self.client_socket._closed:
                try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except (OSError, socket.error):
                    pass
                try:
                    self.client_socket.close()
                except (OSError, socket.error):
                    pass

            #If the threads havent finished their blocking operation, there are errors. So I put a timeout of 2 seconds to wait for the operations to finish
            if hasattr(self, 'readThread'): #hasattr checks if there is a read thread and returns true if exists.
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
            self.logger.info("Connection terminated")


    def start(self):
        self.logger.info("Read and Write Threads Started...")
        self.readThread.start()
        self.writeThread.start()

    def pushMessage(self, message_dict):
        try:
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

