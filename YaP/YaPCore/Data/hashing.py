
import hashlib

def hash_pwd_nosalt(pwd, cycles=150000):
    
    h = hashlib.blake2b(digest_size=64)

    for _ in range(cycles):

        h.update(pwd)

    return h.digest()

def hash_pwd(pwd, salt, cycles=150000):

    h = hashlib.blake2b(digest_size=64)

    for _ in range(cycles):

        h.update(pwd+salt)

    return h.digest()

def hash_str(txt):

    return hashlib.sha256(txt.encode('utf-8')+b'Shit').hexdigest()