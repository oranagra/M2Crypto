"""M2Crypto wrapper for OpenSSL EVP API.

Copyright (c) 1999-2004 Ng Pheng Siong. All rights reserved."""

RCS_id='$Id: EVP.py,v 1.10 2004/04/12 02:04:19 ngps Exp $'

import Err, util
import m2

class MessageDigest:
    """
    Message Digest
    """
    def __init__(self, algo):
        md = getattr(m2, algo)
        if not md:
            raise ValueError, ('unknown algorithm', algo)
        self.md=md()
        self.ctx=m2.md_ctx_new()
        m2.digest_init(self.ctx, self.md)

    def __del__(self):
        if self.ctx:
            m2.md_ctx_free(self.ctx)

    def update(self, data):
        m2.digest_update(self.ctx, data)

    def final(self):
        return m2.digest_final(self.ctx)

    # Deprecated.
    digest = final 


class HMAC:
    def __init__(self, key, algo='sha1'):
        md = getattr(m2, algo)
        if not md:
            raise ValueError, ('unknown algorithm', algo)
        self.md=md()
        self.ctx=m2.hmac_ctx_new()
        m2.hmac_init(self.ctx, key, self.md)

    def __del__(self):
        if self.ctx:
            m2.hmac_ctx_free(self.ctx)

    def reset(self, key):
        m2.hmac_init(self.ctx, key, self.md)

    def update(self, data):
        m2.hmac_update(self.ctx, data)

    def final(self):
        return m2.hmac_final(self.ctx)
    
    digest=final

def hmac(key, data, algo='sha1'):
    md = getattr(m2, algo)
    if not md:
        raise ValueError, ('unknown algorithm', algo)
    return m2.hmac(key, data, md())


class Cipher:
    def __init__(self, alg, key, iv, op, key_as_bytes=0, d='md5', salt='12345678', i=1):
        cipher = getattr(m2, alg)
        if not cipher:
            raise ValueError, ('unknown cipher', alg)
        self.cipher=cipher()
        if key_as_bytes:
            kmd = getattr(m2, d)
            if not kmd:
                raise ValueError, ('unknown message digest', d)
            key = m2.bytes_to_key(self.cipher, kmd(), key, salt, iv, i)
        self.ctx=m2.cipher_ctx_new()
        m2.cipher_init(self.ctx, self.cipher, key, iv, op)
        del key

    def __del__(self):
        if self.ctx:
            m2.cipher_ctx_free(self.ctx)

    def update(self, data):
        return m2.cipher_update(self.ctx, data)

    def final(self):
        return m2.cipher_final(self.ctx)


class PKey:
    """
    Public Key
    """
    def __init__(self, pkey=None, _pyfree=0, md='sha1'):
        if pkey is not None:
            self.pkey = pkey
            self._pyfree = _pyfree
        else:
            self.pkey = m2.pkey_new()
            self._pyfree = 1
        self._set_context(md)

    def __del__(self):
        if self._pyfree:
            m2.pkey_free(self.pkey)
        m2.md_ctx_free(self.ctx)

    def _ptr(self):
        return self.pkey

    def _set_context(self, md):
        mda = getattr(m2, md)
        if not mda:
            raise ValueError, ('unknown message digest', md)
        self.md = mda()
        self.ctx = m2.md_ctx_new()

    def reset_context(self, md='sha1'):
        """
        Reset internal message digest context.

        @type md: string
        @param md: The message digest algorithm.
        """
        self._set_context(md)

    def sign_init(self):
        """
        Initialise signing operation with self.
        """
        m2.sign_init(self.ctx, self.md)

    def sign_update(self, data):
        """
        Feed data to signing operation.

        @type data: string
        @param data: Data to be signed.
        """
        m2.sign_update(self.ctx, data)

    def sign_final(self):
        """
        Return signature.

        @rtype: string
        @return: The signature.
        """
        return m2.sign_final(self.ctx, self.pkey)

    # Deprecated
    update = sign_update
    final = sign_final

    def verify_init(self):
        """
        Initialise signature verification operation with self.
        """
        m2.verify_init(self.ctx, self.md)

    def verify_update(self, data):
        """
        Feed data to verification operation.

        @type data: string
        @param data: Data to be verified.
        """
        m2.verify_update(self.ctx, data)

    def verify_final(self):
        """
        Return result of verification.

        @rtype: int
        @return: Result of verification: 1 for success, 0 for failure.
        """
        return m2.verify_final(self.ctx, None, self.pkey)

    def assign_rsa(self, rsa):
        """
        Assign the RSA key pair to self.

        @type rsa: M2Crypto.RSA.RSA
        @param rsa: M2Crypto.RSA.RSA object to be assigned to self.

        @rtype: int
        @return: Return 1 for success and 0 for failure.
        """
        ret = m2.pkey_assign_rsa(self.pkey, rsa.rsa)
        if ret:
            rsa._pyfree = 0
        return ret

    def save_key(self, file, cipher='aes_128_cbc', callback=util.passphrase_callback):
        """
        Save the key pair to a file in PEM format.

        @type file: string
        @param file: Name of file to save key to.

        @type cipher: string
        @param cipher: Symmetric cipher to protect the key. The default
        cipher is 'aes_128_cbc'. If cipher is None, then the key is saved
        in the clear.

        @type callback: Python callable
        @param callback: A Python callable object that is invoked
        to acquire a passphrase with which to protect the key. 
        The default is util.passphrase_callback.
        """
        bio = BIO.openfile(file, 'wb')
        return self.save_key_bio(bio, cipher, callback)

    def save_key_bio(self, bio, cipher='aes_128_cbc', callback=util.passphrase_callback):
        """
        Save the key pair to the M2Crypto.BIO object 'bio' in PEM format.

        @type bio: M2Crypto.BIO
        @param bio: M2Crypto.BIO object to save key to.

        @type cipher: string
        @param cipher: Symmetric cipher to protect the key. The default
        cipher is 'aes_128_cbc'. If cipher is None, then the key is saved
        in the clear.

        @type callback: Python callable
        @param callback: A Python callable object that is invoked
        to acquire a passphrase with which to protect the key. 
        The default is util.passphrase_callback.
        """
        if cipher is None:
            return m2.pkey_write_pem_no_cipher(self.pkey, bio._ptr(), callback)
        else:
            ciph = getattr(m2, cipher, None)
            if ciph is None:
                raise EVPError, 'not such cipher %s' % cipher
            else:
                ciph = ciph()
            return m2.pkey_write_pem(self.pkey, bio._ptr(), ciph, callback)

    def as_pem(self, cipher='aes_128_cbc', callback=util.passphrase_callback):
        """
        Return key in PEM format in a string.

        @type cipher: string
        @param cipher: Symmetric cipher to protect the key. The default
        cipher is 'aes_128_cbc'. If cipher is None, then the key is saved
        in the clear.

        @type callback: Python callable
        @param callback: A Python callable object that is invoked
        to acquire a passphrase with which to protect the key. 
        The default is util.passphrase_callback.
        """
        bio = BIO.MemoryBuffer()
        self.save_key_bio(bio, cipher, callback)
        return bio.read_all()


def load_key(file, callback=util.passphrase_callback):
    """
    Load an M2Crypto.EVP.PKey from file.

    @type file: string
    @param file: Name of file containing the key in PEM format.

    @type callback: Python callable
    @param callback: A Python callable object that is invoked
    to acquire a passphrase with which to protect the key.

    @rtype: M2Crypto.EVP.PKey
    @return: M2Crypto.EVP.PKey object.
    """
    bio = m2.bio_new_file(file, 'r')
    if bio is None:
        raise Err.get_error()
    cptr = m2.pkey_read_pem(bio, callback)
    m2.bio_free(bio)
    if cptr is None:
        raise Err.get_error()
    return PKey(cptr, 1)

def load_key_bio(bio, callback=util.passphrase_callback):
    """
    Load an M2Crypto.EVP.PKey from an M2Crypto.BIO object.

    @type bio: M2Crypto.BIO
    @param file: M2Crypto.BIO object containing the key in PEM format.

    @type callback: Python callable
    @param callback: A Python callable object that is invoked
    to acquire a passphrase with which to protect the key.

    @rtype: M2Crypto.EVP.PKey
    @return: M2Crypto.EVP.PKey object.
    """
    cptr = m2.pkey_read_pem(bio._ptr(), callback)
    if cptr is None:
        raise Err.get_error()
    return PKey(cptr, 1)

def load_key_string(string, callback=util.passphrase_callback):
    """
    Load an M2Crypto.EVP.PKey from a string.

    @type string: string
    @param file: String containing the key in PEM format.

    @type callback: Python callable
    @param callback: A Python callable object that is invoked
    to acquire a passphrase with which to protect the key.

    @rtype: M2Crypto.EVP.PKey
    @return: M2Crypto.EVP.PKey object.
    """
    bio = BIO.MemoryBuffer(string)
    return load_key_bio( bio, callback)

