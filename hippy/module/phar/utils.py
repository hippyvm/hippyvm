from hippy.module import phpstruct


def read_manifest(interp, data):
    """
    4 bytes: Filename length in bytes
    ?? :  Filename (length specified in previous)
    4 bytes: Un-compressed file size in bytes
    4 bytes: Unix timestamp of file
    4 bytes: Compressed file size in bytes
    4 bytes: CRC32 checksum of un-compressed file contents
    4 bytes: Bit-mapped File-specific flags
    4 bytes: Serialized File Meta-data length (0 for none)
    ?? :  Serialized File Meta-data, stored in serialize() format
    """
    filename_len = phpstruct.Unpack(interp.space, "N", data).build()[0][-1].unwrap()
    input_format = "Nfilename_len/a%dfilename/Nuncompressed_filesize/Ntimestamp\
/Ncompressed_filesize/Ncrc32/Nflags/Nmetadata_len" % filename_len
    item_list = phpstruct.Unpack(interp.space,
                                 input_format,
                                 data).build()
    # N or V?
    # TODO: Read serialized file metadata
    result = {}
    for k, w_v in item_list:
        result[k[1:]] = w_v.unwrap()
    return result
