from collections import OrderedDict
from hippy.objspace import w_False
from hippy.builtin import (
    wrap, Optional, Resource, FilenameArg, StreamContextArg,
    ExitFunctionWithError)
from hippy.module.standard.file.funcs import _valid_fname
from rpython.rlib.objectmodel import we_are_translated

from hippy.module.hash.resources import W_HashResource
from hippy.module.hash.hash_klass import (HashClass, MD2Hash, MD4Hash, MD5Hash,
                                        RIPEMD128Hash,
                                        RIPEMD160Hash, RIPEMD256Hash,
                                        RIPEMD320Hash, HAVAL128_3Hash,
                                        HAVAL128_4Hash, HAVAL128_5Hash,
                                        HAVAL160_3Hash, HAVAL160_4Hash,
                                        HAVAL160_5Hash, HAVAL192_3Hash,
                                        HAVAL192_4Hash, HAVAL192_5Hash,
                                        HAVAL224_3Hash, HAVAL224_4Hash,
                                        HAVAL224_5Hash,  HAVAL256_3Hash,
                                        HAVAL256_4Hash, HAVAL256_5Hash,
                                        WHIRLPOOLHash,
                                        TIGER128_3Hash, TIGER160_3Hash,
                                        TIGER192_3Hash,
                                        TIGER128_4Hash, TIGER160_4Hash,
                                        TIGER192_4Hash,
                                        SHA1Hash,
                                        SHA224Hash, SHA256Hash,
                                        SHA384Hash, SHA512Hash,
                                        CRC32Hash, CRC32BHash, GOSTHash,
                                        SNEFRU256Hash,
                                        JOAATHash, ADLER32Hash,
                                        FNV132Hash, FNV164Hash)

_hash_algos = OrderedDict({
    'md2': MD2Hash,
    'md4': MD4Hash,
    'md5': MD5Hash,

    'sha1': SHA1Hash,
    'sha224': SHA224Hash,
    'sha256': SHA256Hash,
    'sha384': SHA384Hash,
    'sha512': SHA512Hash,

    'crc32': CRC32Hash,
    'crc32b': CRC32BHash,

    'snefru': SNEFRU256Hash,
    'snefru256': SNEFRU256Hash,

    'gost': GOSTHash,

    'whirlpool': WHIRLPOOLHash,
    'tiger128,3': TIGER128_3Hash,
    'tiger160,3': TIGER160_3Hash,
    'tiger192,3': TIGER192_3Hash,
    'tiger128,4': TIGER128_4Hash,
    'tiger160,4': TIGER160_4Hash,
    'tiger192,4': TIGER192_4Hash,

    'joaat': JOAATHash,
    'adler32': ADLER32Hash,

    'fnv132': FNV132Hash,
    'fnv164': FNV164Hash,

    'ripemd': RIPEMD128Hash,
    'ripemd128': RIPEMD128Hash,
    'ripemd160': RIPEMD160Hash,
    'ripemd256': RIPEMD256Hash,
    'ripemd320': RIPEMD320Hash,

    'haval128,3': HAVAL128_3Hash,
    'haval128,4': HAVAL128_4Hash,
    'haval128,5': HAVAL128_5Hash,

    'haval160,3': HAVAL160_3Hash,
    'haval160,4': HAVAL160_4Hash,
    'haval160,5': HAVAL160_5Hash,

    'haval192,3': HAVAL192_3Hash,
    'haval192,4': HAVAL192_4Hash,
    'haval192,5': HAVAL192_5Hash,

    'haval224,3': HAVAL224_3Hash,
    'haval224,4': HAVAL224_4Hash,
    'haval224,5': HAVAL224_5Hash,

    'haval256,3': HAVAL256_3Hash,
    'haval256,4': HAVAL256_4Hash,
    'haval256,5': HAVAL256_5Hash,

})


def _get_hash_algo(algo):
    try:
        return _hash_algos[algo]()
    except KeyError:
        raise ExitFunctionWithError("Unknown hashing algorithm: %s" % algo,
            return_value=w_False)


def strxor(s0, s1):
    l = []
    for x in range(min(len(s0), len(s1))):
        a = s0[x]
        b = s1[x]
        l.append(chr(ord(a) ^ ord(b)))
    # l = [chr(ord(a) ^ ord(b)) for a, b in zip(s0, s1)]
    return ''.join(l)


def hmac(algo, key, data, raw_output):
    h = _get_hash_algo(algo)
    bs = h.block_size
    ipad = [chr(0x36)] * bs
    opad = [chr(0x5c)] * bs
    if len(key) > bs:
        h.update(key)
        key = h.digest()
    elif len(key) < bs:
        key = key + chr(0) * (bs - len(key))

    inside = _get_hash_algo(algo)
    outside = _get_hash_algo(algo)

    inside.update(strxor(key, ipad))
    inside.update(data)
    outside.update(strxor(key, opad))
    outside.update(inside.digest())
    if raw_output:
        return outside.digest()
    return outside.hexdigest()


@wrap(['space'])
def hash_algos(space):
    """ Return a list of registered hashing algorithms"""
    l = ['md2', 'md4', 'md5',
         'sha1', 'sha224', 'sha256', 'sha384', 'sha512',
         'ripemd128', 'ripemd160', 'ripemd256', 'ripemd320',
         'whirlpool',
         'tiger128,3', 'tiger160,3', 'tiger192,3',
         'tiger128,4', 'tiger160,4', 'tiger192,4',
         'snefru', 'snefru256',
         'gost', 'adler32', 'crc32', 'crc32b',
         'fnv132', 'fnv164', 'joaat',
         'haval128,3', 'haval160,3', 'haval192,3', 'haval224,3', 'haval256,3',
         'haval128,4', 'haval160,4', 'haval192,4', 'haval224,4', 'haval256,4',
         'haval128,5', 'haval160,5', 'haval192,5', 'haval224,5', 'haval256,5',
    ]
    return space.new_array_from_list([space.newstr(s) for s in l])


@wrap(['space', Resource(W_HashResource, True)])
def hash_copy(space, w_res):
    """ Copy hashing context"""
    return w_res.deepcopy()


@wrap(['space', str, FilenameArg(None), Optional(bool)])
def hash_file(space, algo, filename, raw_output=False):
    """ Generate a hash value using the contents of a given file"""
    h = _get_hash_algo(algo)
    if not _valid_fname(filename):
        space.ec.warn("hash_file() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_Null
    try:
        f = open(filename)
        while True:
            data = f.read(1024)
            if not data:
                break
            h.update(data)
    except IOError, e:
        if not we_are_translated():
            space.ec.warn("hash_file(%s): failed to open stream: "
                          "%s" % (filename, e.strerror))
            return space.w_False
        assert False  # RPython does not raise IOError
    except OSError:
        return space.w_False
    if raw_output:
        return space.wrap(h.digest())
    return space.wrap(h.hexdigest())


@wrap(['space', str, Optional(int), Optional(str)])
def hash_init(space, algo, options=0, key=None):
    """ Initialize an incremental hashing context"""
    h = _get_hash_algo(algo)
    assert isinstance(h, HashClass)
    if options == 1:
        bs = h.block_size
        if len(key) > bs:
            h.update(key)
            key = h.digest()
            h.__init__()
        else:
            key = key + chr(0) * (bs - len(key))

        ipad = [chr(0x36)] * bs
        key = strxor(key, ipad)
        h.update(key)
    return W_HashResource(space, h, options, key)


@wrap(['space', Resource(W_HashResource, True), Optional(bool)])
def hash_final(space, w_res, raw_output=False):
    """ Finalize an incremental hash and return resulting digest"""
    if w_res.options == 1:
        digest = w_res.digest()
        bs = w_res.hashinst.block_size
        key = w_res.key

        opad = [chr(0x6A)] * bs
        w_res.hashinst.__init__()
        w_res.update(strxor(key, opad))
        w_res.update(digest)
    if raw_output:
        return space.wrap(w_res.digest())
    return space.wrap(w_res.hexdigest())


@wrap(['space', str, str, str, Optional(bool)])
def hash_hmac_file(space, algo, filename, key, raw_output=False):
    """ Generate a keyed hash value using the
    HMAC method and the contents of a given file"""

    if not _valid_fname(filename):
        space.ec.warn("hash_hmac_file() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_False

    h = _get_hash_algo(algo)
    bs = h.block_size
    ipad = [chr(0x36)] * bs
    opad = [chr(0x5c)] * bs

    if len(key) > bs:
        h.update(key)
        key = h.digest()
    elif len(key) < bs:
        key = key + chr(0) * (bs - len(key))

    inside = _get_hash_algo(algo)
    outside = _get_hash_algo(algo)

    inside.update(strxor(key, ipad))

    try:
        f = open(filename)

        while True:
            data = f.read(1024)
            if not data:
                break
            inside.update(data)
    except IOError, e:
        if not we_are_translated():
            space.ec.warn("hash_file(%s): failed to open stream: "
                          "%s" % (filename, e.strerror))
            return space.w_False
        assert False  # RPython does not raise IOError
    except OSError:
        return space.w_False

    outside.update(strxor(key, opad))
    outside.update(inside.digest())
    if raw_output:
        return space.wrap(outside.digest())
    return space.wrap(outside.hexdigest())


@wrap(['space', str, str, str, Optional(bool)])
def hash_hmac(space, algo, data, key, raw_output=False):
    """ Generate a keyed hash value using the HMAC method"""
    h = _get_hash_algo(algo)
    res = hmac(algo, key, data, raw_output)
    return space.wrap(res)


def hash_pbkdf2():
    """ Generate a PBKDF2 key derivation of a supplied password"""
    return NotImplementedError()


@wrap(['space', Resource(W_HashResource, True), FilenameArg(None),
       Optional(StreamContextArg(None))])
def hash_update_file(space, w_res, filename, w_ctx=None):
    """ Pump data into an active hashing context from a file"""
    if not _valid_fname(filename):
        space.ec.warn("hash_file() expects parameter 1 "
                      "to be a valid path, string given")
        return space.w_False
    try:
        f = open(filename)

        while True:
            data = f.read(1024)
            if not data:
                break
            w_res.update(data)
    except IOError, e:
        if not we_are_translated():
            space.ec.warn("hash_file(%s): failed to open stream: "
                          "%s" % (filename, e.strerror))
            return space.w_False
        assert False  # RPython does not raise IOError
    except OSError:
        return space.w_False


def hash_update_stream():
    """ Pump data into an active hashing context from an open stream"""
    return NotImplementedError()


@wrap(['space', Resource(W_HashResource, True), str])
def hash_update(space, w_res, data):
    """ Pump data into an active hashing context"""
    w_res.update(data)
    return space.w_True


@wrap(['space', str, str, Optional(bool)])
def hash(space, algo, data, raw_output=False):
    """ Generate a hash value (message digest)"""
    h = _get_hash_algo(algo)
    h.update(data)
    if raw_output:
        return space.wrap(h.digest())
    return space.wrap(h.hexdigest())
