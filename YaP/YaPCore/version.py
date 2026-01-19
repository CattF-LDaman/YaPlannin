
VERSION = (0,0,1)
VERSION_BYTES = b"".join(v.to_bytes(1,"little") for v in VERSION)

VERSION_IDENTIFIER = "Shizzle"
VERSION_STRING = ".".join(str(v) for v in VERSION)+" "+VERSION_IDENTIFIER
VERSION_STRING_SIMPLE = ".".join(str(v) for v in VERSION)
BUILD = "dev"

def version_from_bytes(vb):

    return tuple([v for v in vb])

def version_to_string(vt):

    return ".".join(str(v) for v in vt)
