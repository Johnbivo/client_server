"""This file contains all encryption classes used in the task management system. (All encryption methods)
The application uses various encrypion methods to provide safe communication between server and clients.

The application uses 4 encryption methods.

Rsa Encryption -> Generates public and private keys for the server. -> Encrypts data using client's public keys -> Decrypts
messages using the server's own private key.

Hash Encryption MD5: This class is actually not used in the server but only in the client.
encrypts data by hashing

CeasarCipher Encryption: This class is not used too, due to the progression of development of this project, decided not to encrypt data using this,
kept it to showcase progression and implementation. Can see the progress of development in the server log.

AES Encryption: Implemented symmetric cryptography using GCM (Galois/Counter Mode). GCM provides both encryption and authentication- meaning the server
knows who he communicates with
It generates a 256-bit encryption key for every client.
Encrypts and decrypts messages using this key.
If client receives the key, he can encrypt and derypt messages too.
"""



import ServerLogger
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP #stands for Public Key Cryptography Standards ,enhances security by adding randomness and structure to the plaintext before encryption
import hashlib
from Crypto.Cipher import AES
import os


class RsaEncryption:
    def __init__(self):
        self.private_key = RSA.generate(2048)
        self.public_key = self.private_key.publickey()

    def getPublicKey(self):
        return self.public_key.export_key()

    def encrypt(self, message, public_key_data):
        try:
            # Check if public_key_data is already an RSA key
            if isinstance(public_key_data, RSA.RsaKey):
                pub_key = public_key_data
            else:
                pub_key = RSA.import_key(public_key_data)

            cipher = PKCS1_OAEP.new(pub_key)
            encrypted_data = cipher.encrypt(message)
            return encrypted_data.hex()
        except Exception as e:
            raise Exception(f"Encryption error: {str(e)}")

    def decrypt(self, hex_message):
        try:
            message_bytes = bytes.fromhex(hex_message)
            cipher = PKCS1_OAEP.new(self.private_key)
            decrypted_data = cipher.decrypt(message_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise Exception(f"Decryption error: {str(e)}")

class HashEncryption:
    def __init__(self, hash_type="md5"):
        self.logger = ServerLogger.server_logger
        self.hash_type = hash_type.lower()

    def _hash(self, input_string):

        hash_object = hashlib.md5()
        hash_object.update(input_string.encode('utf-8'))
        self.logger.debug("Password encrypted")
        return hash_object.hexdigest()


    def encrypt_password(self, password):
        return self._hash(password)


class CaesarCipher:
    def __init__(self):
        self.encrypted_text = ""
        self.decrypted_text = ""
        self.logger = ServerLogger.server_logger


    def encrypt_text(self, text, shift):
        self.encrypted_text = ""
        for character in text:
            if isinstance(character, str) and len(character) == 1:
                if ord(character) >= 65 and ord(character) <= 90:
                    new_character = chr((ord(character) - 65 + shift) % 26 + 65)
                    self.encrypted_text += new_character
                elif ord(character) >= 97 and ord(character) <= 122:
                    new_character = chr((ord(character) - 97 + shift) % 26 + 97)
                    self.encrypted_text += new_character
                elif ord(character) >= 48 and ord(character) <= 57:
                    new_character = chr((ord(character) - 48 + shift) % 10 + 48)
                    self.encrypted_text += new_character
                elif ord(character) >= 32 and ord(character) <= 47:
                    new_character = chr((ord(character) - 32 + shift) % 16 + 32)
                    self.encrypted_text += new_character
                else:

                    self.encrypted_text += character
            else:
                print(f"Skipping invalid character: {character}")

        return self.encrypted_text

    def decrypt_text(self, text, shift):
        self.decrypted_text = ""
        for character in text:
            if isinstance(character, str) and len(character) == 1:
                if ord(character) >= 65 and ord(character) <= 90:
                    new_character = chr((ord(character) - 65 - shift) % 26 + 65)
                    self.decrypted_text += new_character
                elif ord(character) >= 97 and ord(character) <= 122:
                    new_character = chr((ord(character) - 97 - shift) % 26 + 97)
                    self.decrypted_text += new_character
                elif ord(character) >= 48 and ord(character) <= 57:  # Digits
                    new_character = chr((ord(character) - 48 - shift) % 10 + 48)
                    self.decrypted_text += new_character
                elif ord(character) >= 32 and ord(character) <= 47:
                    new_character = chr((ord(character) - 32 - shift) % 16 + 32)
                    self.decrypted_text += new_character
                else:
                    self.decrypted_text += character
            else:
                self.logger.info(f"Skipping invalid character: {character}")
        return self.decrypted_text




class AESencryption:
    def __init__(self):
        self.logger = ServerLogger.server_logger
        self.key = os.urandom(32)


    def encrypt_text(self, text):
        if isinstance(text, str):
            text = text.encode('utf-8')

        aesCipher = AES.new(self.key, AES.MODE_GCM)
        ciphertext, authTag = aesCipher.encrypt_and_digest(text)
        self.logger.debug(f"Text encrypted AES")
        return ciphertext, aesCipher.nonce, authTag


    def decrypt_text(self, encrypted_text):
        (ciphertext, nonce, authTag) = encrypted_text
        aesCipher = AES.new(self.key, AES.MODE_GCM,nonce)
        text = aesCipher.decrypt_and_verify(ciphertext, authTag)
        self.logger.debug(f"Text decrypted AES")
        return text.decode('utf-8')


    def get_key(self):
        return self.key


