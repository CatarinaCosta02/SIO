from __future__ import annotations

import random
import secrets
import PyKCS11

from cryptography import x509
from cryptography.hazmat.backends import default_backend as db
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import SHA1, Hash

PKCS11_LIB = '/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so'


class KeyChain:

    def __init__(self, asymmetric_key_size, symmetric_key_size, prob_cheat=0.0, cc=False):
        self.asymmetric_key_size = asymmetric_key_size
        self.symmetric_key_size = symmetric_key_size
        self.prob_cheat = prob_cheat
        self.logger = None
        # Generated
        self.private_key = None
        self.private_key_pem = None
        self.public_key = None
        self.public_key_pem = None
        self.symmetric_key = None
        # Users
        self.user_public_key_pems = {}
        # Citizen card
        self.cc = cc
        self.session_0 = None
        self.session_1 = None
        self.private_key_cc = None
        self.cert_cc = None

    def get_user_public_key_pem(self, nickname: str):
        return self.user_public_key_pems.get(nickname, None)

    def set_user_public_key_pem(self, nickname: str, public_key_pem: bytes):
        self.user_public_key_pems[nickname] = public_key_pem

    def clear_user_public_key_pems(self):
        self.user_public_key_pems = {}

    """Assymmetric"""

    def generate_asymmetric(self):
        """Generates an assymmetric key pair to sign messages."""
        # Generate key pair
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=8 * self.asymmetric_key_size
        )
        self.public_key = self.private_key.public_key()
        # PEM representation
        self.private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def sign(self, m: bytes) -> bytes:
        """Signs a message with the private key."""
        signature = self.private_key.sign(m, padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ), hashes.SHA256())
        # CHEATING
        if random.random() < self.prob_cheat:
            i = random.randint(0, len(signature) - 1)
            signature = signature[:i] + secrets.token_bytes(1) + signature[i + 1:]
            self.logger.log(f'[CHEAT] CHEATING: Changing a random byte ({i}) in the signature.')
        return signature

    @classmethod
    def verify(cls, m: bytes, sm: bytes, public_key_pem: bytes) -> bool:
        """Verifies a signature with the public key."""
        public_key = serialization.load_pem_public_key(public_key_pem, backend=None)
        try:
            public_key.verify(sm, m, padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ), hashes.SHA256())
            return True
        except:
            return False

    """Symmetric"""

    def generate_symmetric(self):
        """Generates a symmetric key to encrypt numbers in the deck."""
        self.symmetric_key = secrets.token_bytes(self.symmetric_key_size)

    def encrypt(self, m: bytes, key=None) -> bytes:
        """Encrypts a message with the symmetric key."""
        if key is None:
            key = self.symmetric_key
        cipher = Cipher(
            algorithm=algorithms.AES(key),
            mode=modes.ECB()
        )
        encryptor = cipher.encryptor()
        return encryptor.update(m) + encryptor.finalize()

    def decrypt(self, c: bytes, key=None) -> bytes:
        """Decrypts a message with the symmetric key."""
        if key is None:
            key = self.symmetric_key
        cipher = Cipher(
            algorithm=algorithms.AES(key),
            mode=modes.ECB()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(c) + decryptor.finalize()

    """Citizen card"""

    def init_cc(self):
        if self.cc:
            pkcs11 = PyKCS11.PyKCS11Lib()
            pkcs11.load(PKCS11_LIB)
            slots = pkcs11.getSlotList(tokenPresent=True)

            # Smartcard is not connected
            if not slots:
                self.logger.log('[ERROR] Smartcard is not connected.')
                exit(1)

            # Slot 0: Contains the certificate
            self.session_0 = pkcs11.openSession(slots[0], PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION)
            self.cert_cc = self.session_0.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE),
                                                       (PyKCS11.CKA_LABEL, 'CITIZEN AUTHENTICATION CERTIFICATE')
                                                       ])[0]

            # Slot 1: Contains the private key and signing mechanism
            self.session_1 = pkcs11.openSession(slots[1], PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION)
            self.logger.log('[INPUT] Sign PIN ("1111" for virtual smartcard): ')
            self.session_1.login(input())
            self.private_key_cc = self.session_1.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
                                                              (PyKCS11.CKA_LABEL, 'CITIZEN SIGNATURE KEY')
                                                              ])[0]

    def sign_cc(self, m: bytes) -> bytes:
        """Signs a message with the citizen card."""
        if self.cc:
            return bytes(self.session_1.sign(
                key=self.private_key_cc,
                data=m,
                mecha=PyKCS11.Mechanism(PyKCS11.CKM_SHA1_RSA_PKCS, None)))
        else:
            return bytes(1)  # Not using citizen card

    def get_cert_cc(self) -> bytes:
        """Gets the citizen card certificate."""
        if self.cc:
            return bytes(self.cert_cc.to_dict()['CKA_VALUE'])
        else:
            return bytes(1)  # Not using citizen card

    @classmethod
    def verify_cc(cls, m: bytes, sm: bytes, cert_cc_bytes: bytes) -> bool:
        """Verifies a signature with the citizen card certificate."""
        if cert_cc_bytes == bytes(1):
            return True  # Not using citizen card

        cert_cc = x509.load_der_x509_certificate(cert_cc_bytes, backend=db())

        # Hash the message
        md = Hash(SHA1(), backend=db())
        md.update(m)
        digest = md.finalize()

        public_key_cc = cert_cc.public_key()
        try:
            public_key_cc.verify(sm, digest, PKCS1v15(), SHA1())
            return True
        except:
            return False
