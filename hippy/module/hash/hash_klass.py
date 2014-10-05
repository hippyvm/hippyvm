from rpython.rtyper.lltypesystem import rffi, lltype
from rpython.rlib.rstring import StringBuilder
from rpython.rlib.objectmodel import specialize

from hippy.module.hash import (
    cfnv, cripemd, ctiger, ccrc32, chaval, cmd, csha, csnefru, cjoaat, cgost,
    cwhirlpool, cadler)


@specialize.argtype(0)
def str2hexstr(arr, size):
    HEXCHARS = ['0', '1', '2', '3', '4', '5', '6', '7',
                '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']

    s = StringBuilder(size)
    for i in range(size):
        s.append(HEXCHARS[(ord(arr[i]) >> 4)])
        s.append(HEXCHARS[(ord(arr[i])) & 15])
    return s.build()


class HashClass(object):

    def __init__(self):
        pass

    def digest(self):
        if self.digest_res:
            return self.digest_res
        return rffi.charpsize2str(self._digest(), self.digest_size)

    def hexdigest(self):
        if self.digest_res:
            return str2hexstr(self.digest_res, self.digest_size)
        return str2hexstr(self._digest(), self.digest_size)

    def update(self, data):
        raise NotImplementedError()


class MD2Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cmd.PTR_MD2_CTX.TO, flavor='raw')
        cmd.c_md2init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 16
        self.block_size = 16
        self.digest_res = None

    def copy(self):
        new = MD2Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cmd.PTR_MD2_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cmd.c_md2final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cmd.c_md2update(self.ctx, ll_data, len(data))


class MD4Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cmd.PTR_MD4_CTX.TO, flavor='raw')
        cmd.c_md4init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 16
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = MD4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cmd.PTR_MD4_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO, self.digest_size, flavor='raw')
        cmd.c_md4final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cmd.c_md4update(self.ctx, ll_data, len(data))


class MD5Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cmd.PTR_MD5_CTX.TO, flavor='raw')
        cmd.c_md5init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 16
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = MD5Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cmd.PTR_MD5_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cmd.c_md5final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cmd.c_md5update(self.ctx, ll_data, len(data))


class RIPEMD128Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cripemd.ptr_ripemd128_ctx.TO, flavor='raw')
        cripemd.c_ripemd128_init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 16
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = RIPEMD128Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cripemd.ptr_ripemd128_ctx.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               16, flavor='raw')
        cripemd.c_ripemd128_final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cripemd.c_ripemd128_update(self.ctx, ll_data, len(data))


class RIPEMD160Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cripemd.ptr_ripemd160_ctx.TO, flavor='raw')
        cripemd.c_ripemd160_init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 20
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = RIPEMD160Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cripemd.ptr_ripemd160_ctx.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               20, flavor='raw')
        cripemd.c_ripemd160_final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cripemd.c_ripemd160_update(self.ctx, ll_data, len(data))


class RIPEMD256Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cripemd.ptr_ripemd256_ctx.TO, flavor='raw')
        cripemd.c_ripemd256_init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 32
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = RIPEMD256Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cripemd.ptr_ripemd256_ctx.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               32, flavor='raw')
        cripemd.c_ripemd256_final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cripemd.c_ripemd256_update(self.ctx, ll_data, len(data))


class RIPEMD320Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cripemd.ptr_ripemd320_ctx.TO, flavor='raw')
        cripemd.c_ripemd320_init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 40
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = RIPEMD320Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cripemd.ptr_ripemd320_ctx.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               40, flavor='raw')
        cripemd.c_ripemd320_final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cripemd.c_ripemd320_update(self.ctx, ll_data, len(data))


class HAVAL128_3Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval3_128init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 16
        self.block_size = 128
        self.digest_res = None

    def copy(self):
        new = HAVAL128_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_128final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            chaval.c_haval_update(self.ctx, ll_data, len(data))


class HAVAL160_3Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval3_160init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 160 / 8
        self.block_size = 128
        self.digest_res = None

    def copy(self):
        new = HAVAL160_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_160final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL192_3Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval3_192init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 192 / 8
        self.block_size = 128
        self.digest_res = None

    def copy(self):
        new = HAVAL192_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_192final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL224_3Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval3_224init(ll_ctx)
        self.ctx = ll_ctx
        self.block_size = 128
        self.digest_size = 224 / 8
        self.digest_res = None

    def copy(self):
        new = HAVAL224_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_224final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL256_3Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval3_256init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 256 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL256_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_256final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL128_4Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval4_128init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 128 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL128_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_128final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL160_4Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval4_160init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 160 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL160_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_160final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL192_4Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval4_192init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 192 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL192_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_192final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL224_4Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval4_224init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 224 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL224_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_224final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL256_4Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval4_256init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 256 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL256_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_256final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL128_5Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval5_128init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 128 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL128_5Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_128final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL160_5Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval5_160init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 160 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL160_5Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_160final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL192_5Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval5_192init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 192 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL192_5Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_192final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL224_5Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval5_224init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 224 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL224_5Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_224final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class HAVAL256_5Hash(HAVAL128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(chaval.HAVAL_CTX_PTR.TO, flavor='raw')
        chaval.c_haval5_256init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 256 / 8
        self.digest_res = None
        self.block_size = 128

    def copy(self):
        new = HAVAL256_5Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(chaval.HAVAL_CTX_PTR.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        chaval.c_haval_256final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class TIGER128_3Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(ctiger.PTR_TIGER_CTX.TO, flavor='raw')
        ctiger.c_TIGER3Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 16
        self.digest_res = None
        self.block_size = 64

    def copy(self):
        new = TIGER128_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ctiger.PTR_TIGER_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               16, flavor='raw')
        ctiger.c_TIGER128Final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            ctiger.c_TIGERUpdate(self.ctx, ll_data, len(data))


class TIGER160_3Hash(TIGER128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(ctiger.PTR_TIGER_CTX.TO, flavor='raw')
        ctiger.c_TIGER3Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 20
        self.digest_res = None
        self.block_size = 64

    def copy(self):
        new = TIGER160_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ctiger.PTR_TIGER_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        ctiger.c_TIGER160Final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class TIGER192_3Hash(TIGER128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(ctiger.PTR_TIGER_CTX.TO, flavor='raw')
        ctiger.c_TIGER3Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 24
        self.digest_res = None
        self.block_size = 64

    def copy(self):
        new = TIGER192_3Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ctiger.PTR_TIGER_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        ctiger.c_TIGER192Final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class TIGER128_4Hash(TIGER128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(ctiger.PTR_TIGER_CTX.TO, flavor='raw')
        ctiger.c_TIGER4Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 16
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = TIGER128_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ctiger.PTR_TIGER_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        ctiger.c_TIGER128Final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class TIGER160_4Hash(TIGER128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(ctiger.PTR_TIGER_CTX.TO, flavor='raw')
        ctiger.c_TIGER4Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 20
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = TIGER160_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ctiger.PTR_TIGER_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        ctiger.c_TIGER160Final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class TIGER192_4Hash(TIGER128_3Hash):

    def __init__(self):
        ll_ctx = lltype.malloc(ctiger.PTR_TIGER_CTX.TO, flavor='raw')
        ctiger.c_TIGER4Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 24
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = TIGER192_4Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ctiger.PTR_TIGER_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        ctiger.c_TIGER192Final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res


class SHA1Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(csha.PTR_SHA1_CTX.TO, flavor='raw')
        csha.c_sha1init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 20
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = SHA1Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(csha.PTR_SHA1_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        csha.c_sha1final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            csha.c_sha1update(self.ctx, ll_data, len(data))


class SHA224Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(csha.PTR_SHA224_CTX.TO, flavor='raw')
        csha.c_sha224init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 28
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = SHA224Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(csha.PTR_SHA224_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        csha.c_sha224final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            csha.c_sha224update(self.ctx, ll_data, len(data))


class SHA256Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(csha.PTR_SHA256_CTX.TO, flavor='raw')
        csha.c_sha256init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 32
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = SHA256Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(csha.PTR_SHA256_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        csha.c_sha256final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            csha.c_sha256update(self.ctx, ll_data, len(data))


class SHA384Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(csha.PTR_SHA384_CTX.TO, flavor='raw')
        csha.c_sha384init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 48
        self.block_size = 128
        self.digest_res = None

    def copy(self):
        new = SHA384Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(csha.PTR_SHA384_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        csha.c_sha384final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            csha.c_sha384update(self.ctx, ll_data, len(data))


class SHA512Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(csha.PTR_SHA512_CTX.TO, flavor='raw')
        csha.c_sha512init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 64
        self.block_size = 128
        self.digest_res = None

    def copy(self):
        new = SHA512Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(csha.PTR_SHA512_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        csha.c_sha512final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            csha.c_sha512update(self.ctx, ll_data, len(data))


class SNEFRU256Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(csnefru.PTR_SNEFRU_CTX.TO, flavor='raw')
        csnefru.c_SNEFRUInit(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 32
        self.block_size = 32
        self.digest_res = None

    def copy(self):
        new = SNEFRU256Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(csnefru.PTR_SNEFRU_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        csnefru.c_SNEFRUFinal(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            csnefru.c_SNEFRUUpdate(self.ctx, ll_data, len(data))


class JOAATHash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cjoaat.PTR_JOAAT_CTX.TO, flavor='raw')
        cjoaat.c_JOAATInit(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 4
        self.block_size = 4
        self.digest_res = None

    def copy(self):
        new = JOAATHash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cjoaat.PTR_JOAAT_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cjoaat.c_JOAATFinal(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cjoaat.c_JOAATUpdate(self.ctx, ll_data, len(data))


class GOSTHash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cgost.PTR_GOST_CTX.TO, flavor='raw')
        cgost.c_GOSTInit(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 32
        self.block_size = 32
        self.digest_res = None

    def copy(self):
        new = GOSTHash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cgost.PTR_GOST_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cgost.c_GOSTFinal(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cgost.c_GOSTUpdate(self.ctx, ll_data, len(data))


class WHIRLPOOLHash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cwhirlpool.PTR_WHIRLPOOL_CTX.TO, flavor='raw')
        cwhirlpool.c_WHIRLPOOLInit(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 64
        self.block_size = 64
        self.digest_res = None

    def copy(self):
        new = WHIRLPOOLHash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cwhirlpool.PTR_WHIRLPOOL_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cwhirlpool.c_WHIRLPOOLFinal(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cwhirlpool.c_WHIRLPOOLUpdate(self.ctx, ll_data, len(data))


class CRC32Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(ccrc32.PTR_CRC32_CTX.TO, flavor='raw')
        ccrc32.c_CRC32Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 4
        self.block_size = 4
        self.digest_res = None

    def copy(self):
        new = CRC32Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ccrc32.PTR_CRC32_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               4, flavor='raw')
        ccrc32.c_CRC32Final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            ccrc32.c_CRC32Update(self.ctx, ll_data, len(data))


class CRC32BHash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(ccrc32.PTR_CRC32_CTX.TO, flavor='raw')
        ccrc32.c_CRC32Init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 4
        self.block_size = 4
        self.digest_res = None

    def copy(self):
        new = CRC32BHash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(ccrc32.PTR_CRC32_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        ccrc32.c_CRC32BFinal(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            ccrc32.c_CRC32BUpdate(self.ctx, ll_data, len(data))


class ADLER32Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cadler.PTR_ADLER32_CTX.TO, flavor='raw')
        cadler.c_adler32init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 4
        self.block_size = 4
        self.digest_res = None

    def copy(self):
        new = ADLER32Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cadler.PTR_ADLER32_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cadler.c_adler32final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cadler.c_adler32update(self.ctx, ll_data, len(data))


class FNV132Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cfnv.PTR_FNV132_CTX.TO, flavor='raw')
        cfnv.c_fnv132init(ll_ctx)
        self.ctx = ll_ctx
        self.digest_size = 4
        self.block_size = 4
        self.digest_res = None

    def copy(self):
        new = FNV132Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cfnv.PTR_FNV132_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cfnv.c_fnv132final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cfnv.c_fnv132update(self.ctx, ll_data, len(data))


class FNV164Hash(HashClass):

    def __init__(self):
        ll_ctx = lltype.malloc(cfnv.PTR_FNV164_CTX.TO, flavor='raw')
        cfnv.c_fnv164init(ll_ctx)
        self.ctx = ll_ctx
        self.block_size = 4
        self.digest_size = 8
        self.digest_res = None

    def copy(self):
        new = FNV164Hash()
        rffi.c_memcpy(rffi.cast(rffi.VOIDP, new.ctx),
                      rffi.cast(rffi.VOIDP, self.ctx),
                      rffi.sizeof(cfnv.PTR_FNV164_CTX.TO))
        return new

    def _digest(self):
        ll_res = lltype.malloc(rffi.CCHARP.TO,
                               self.digest_size, flavor='raw')
        cfnv.c_fnv164final(ll_res, self.ctx)
        self.digest_res = rffi.charpsize2str(ll_res, self.digest_size)
        return ll_res

    def update(self, data):
        with rffi.scoped_str2charp(data) as ll_data:
            cfnv.c_fnv164update(self.ctx, ll_data, len(data))
