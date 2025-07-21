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



from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import hashlib
import ClientLogger
from Crypto.Cipher import AES
import os


class HashEncryption:
    def __init__(self):
        self.logger = ClientLogger.client_logger

    def encrypt_password(self, password: str) -> str:
        hash_object = hashlib.md5()
        hash_object.update(password.encode('utf-8'))
        return hash_object.hexdigest()


class CaesarCipher:
    def __init__(self):
        self.encrypted_text = ""
        self.shift = 10
        self.logger = ClientLogger.client_logger

    def encrypt_username(self, text):
        self.encrypted_text = ""
        for character in text:
            if isinstance(character, str) and len(character) == 1:
                if ord(character) >= 65 and ord(character) <= 90:  # Uppercase letters
                    new_character = chr((ord(character) - 65 + self.shift) % 26 + 65)
                    self.encrypted_text += new_character
                elif ord(character) >= 97 and ord(character) <= 122:  # Lowercase letters
                    new_character = chr((ord(character) - 97 + self.shift) % 26 + 97)
                    self.encrypted_text += new_character
                elif ord(character) >= 48 and ord(character) <= 57:  # Digits
                    new_character = chr((ord(character) - 48 + self.shift) % 10 + 48)
                    self.encrypted_text += new_character
                elif ord(character) >= 32 and ord(character) <= 47:  # Punctuation and space
                    new_character = chr((ord(character) - 32 + self.shift) % 16 + 32)
                    self.encrypted_text += new_character
                else:
                    self.encrypted_text += character
        return self.encrypted_text

    def decrypt_username(self, text):
        self.decrypted_text = ""
        for character in text:
            if isinstance(character, str) and len(character) == 1:
                if ord(character) >= 65 and ord(character) <= 90:
                    new_character = chr((ord(character) - 65 - self.shift) % 26 + 65)
                    self.decrypted_text += new_character
                elif ord(character) >= 97 and ord(character) <= 122:
                    new_character = chr((ord(character) - 97 - self.shift) % 26 + 97)
                    self.decrypted_text += new_character
                elif ord(character) >= 48 and ord(character) <= 57:
                    new_character = chr((ord(character) - 48 - self.shift) % 10 + 48)
                    self.decrypted_text += new_character
                elif ord(character) >= 32 and ord(character) <= 47:
                    new_character = chr((ord(character) - 32 - self.shift) % 16 + 32)
                    self.decrypted_text += new_character
                else:
                    self.decrypted_text += character
            else:
                self.logger.info(f"Skipping invalid character: {character}")
        return self.decrypted_text


class RsaEncryption:
    def __init__(self):
        self.logger = ClientLogger.client_logger
        self.private_key = RSA.generate(2048)
        self.public_key = self.private_key.publickey()

    def getPublicKey(self):
        return self.public_key.export_key()

    def decrypt(self, hex_message: str) -> str:
        try:
            message_bytes = bytes.fromhex(hex_message)
            cipher = PKCS1_OAEP.new(self.private_key)
            decrypted_data = cipher.decrypt(message_bytes)
            return decrypted_data
        except Exception as e:
            self.logger.error(f"Decryption error: {e}")
            raise

    def encrypt(self, message: bytes, pub_key) -> str:
        """Encrypts bytes and returns hex string"""
        try:
            cipher = PKCS1_OAEP.new(RSA.import_key(pub_key))
            encrypted_data = cipher.encrypt(message)
            return encrypted_data.hex()
        except Exception as e:
            self.logger.error(f"Encryption error: {e}")
            raise


class AESencryption:
    def __init__(self):
        self.logger = ClientLogger.client_logger
        self.key = os.urandom(32)

    def encrypt_text(self, text):
        if isinstance(text, str):
            text = text.encode('utf-8')

        aesCipher = AES.new(self.key, AES.MODE_GCM)
        ciphertext, authTag = aesCipher.encrypt_and_digest(text)
        self.logger.debug(f"Text encrypted AES")
        return (ciphertext, aesCipher.nonce, authTag)

    def decrypt_text(self, encrypted_text):
        (ciphertext, nonce, authTag) = encrypted_text
        aesCipher = AES.new(self.key, AES.MODE_GCM, nonce)
        text = aesCipher.decrypt_and_verify(ciphertext, authTag)
        self.logger.debug(f"Text decrypted AES")
        return text.decode('utf-8')

    def get_key(self):
        return self.key

    #Needed to make a function set, to initialize the key in the connectionHandler
    def set_key(self, key):
        self.key = key