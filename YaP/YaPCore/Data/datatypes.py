
import json
import io

D_BOOL = 111
D_INT8 = 0
D_INT16 = 1
D_INT32 = 2
D_INT64 = 3
D_INT8S = 4
D_INT16S = 5
D_INT32S = 6
D_INT64S = 7
D_STRING = 8
D_JSON = 9
D_RAW = 11
D_RGB = 12
D_DATA = 13
D_KSTR = 14
D_INT128 = 20
D_INT128S = 21
D_DEC = 22
D_DECS = 23
D_DDICT = 25

def pack_bool(data):

    return b'\x01' if data else b'\x00'

def unpack_bool(data):

    return bool(data[0])

def pack_int(data, intsize):

    return data.to_bytes(intsize,"little")

def unpack_int(data):

    return int.from_bytes(data, "little")

def pack_int8(data):

    return pack_int(data, 1)

def pack_int16(data):

    return pack_int(data, 2)

def pack_int32(data):

    return pack_int(data, 4)

def pack_int64(data):

    return pack_int(data, 8)

def pack_int128(data):

    return pack_int(data, 16)

def pack_int_s(data, intsize):

    return data.to_bytes(intsize,"little", signed=True)

def unpack_int_s(data):

    return int.from_bytes(data, "little", signed=True)

def pack_int8_s(data):

    return pack_int_s(data, 1)

def pack_int16_s(data):

    return pack_int_s(data, 2)

def pack_int32_s(data):

    return pack_int_s(data, 4)

def pack_int64_s(data):

    return pack_int_s(data, 8)

def pack_int128_s(data):

    return pack_int_s(data, 16)

def pack_string(data):

    return data.encode('utf-8')

def unpack_string(data):

    return data.decode('utf-8')

def pack_json(data):

    return json.dumps(data).encode('utf-8')

def unpack_json(data):

    return json.loads(data.decode('utf-8'))

def raw(data):

    return data

def pack_rgb(data):

    return pack_int8(data[0])+pack_int8(data[1])+pack_int8(data[2])

def unpack_rgb(data):
    
    return [data[0], data[1], data[2]]

def pack_datastruc(data):
    from YaP.YaPCore.Data.struc import build_struc

    struc, strucdata = data
    out = io.BytesIO()

    for dataname, datatype, *datalen in struc:  # datalen is actually a list of 'other arguments'

        out.write(len(dataname).to_bytes(1,"little")+dataname.encode('ascii'))
        out.write(datatype.to_bytes(1,'little'))
        if datatype in DATATYPES and not DATATYPES[datatype][2]:
            out.write(datalen[0].to_bytes(1,"little"))
    struclen = len(out.getvalue())
    out.write(build_struc(struc, strucdata))

    return struclen.to_bytes(2,"little")+out.getvalue()

def unpack_datastruc(data):
    from YaP.YaPCore.Data.struc import read_struc

    d = io.BytesIO(data)
    
    struc_len = int.from_bytes(d.read(2),'little')
    struc = []

    while d.tell() < struc_len:
        
        _data = []
        dataname_len = d.read(1)[0]
        _data.append(dataname := d.read(dataname_len).decode('utf-8'))
        _data.append(datatype := d.read(1)[0])
        if datatype in DATATYPES and not DATATYPES[datatype][2]:
            _data.append(datalen := d.read(1)[0])
        struc.append(_data)

    return read_struc(struc, d.read())

def unpack_datastruc_dict(data):

    return unpack_datastruc(data).__dict__

def pack_keystrings(data):
    dstruc = [(k, D_STRING, 4) for k in data]
    
    return pack_datastruc((dstruc, data))

def pack_dec(data):

    return pack_int128(int(data*1000))

def unpack_dec(data):

    return unpack_int(data)/1000

def pack_decs(data):

    return pack_int128_s(int(data*1000))

def unpack_decs(data):

    return unpack_int_s(data)/1000

DT_PACK = 0
DT_UNPACK = 1
DT_SIZE = 2

DATATYPES = {

D_BOOL: (pack_bool, unpack_bool, 1),
D_INT8: (pack_int8, unpack_int, 1),
D_INT16: (pack_int16, unpack_int, 2),
D_INT32: (pack_int32, unpack_int, 4),
D_INT64: (pack_int64, unpack_int, 8),
D_INT128: (pack_int128, unpack_int, 16),
D_INT8S: (pack_int8_s, unpack_int_s, 1),
D_INT16S: (pack_int16_s, unpack_int_s, 2),
D_INT32S: (pack_int32_s, unpack_int_s, 4),
D_INT64S: (pack_int64_s, unpack_int_s, 8),
D_INT128S: (pack_int128_s, unpack_int_s, 16),
D_STRING: (pack_string, unpack_string, None), # None marks non-fixed length
D_JSON: (pack_json, unpack_json, None),
D_RAW: (raw, raw, None),
D_RGB: (pack_rgb, unpack_rgb, 3),
D_DATA: (pack_datastruc, unpack_datastruc, None), # struc, dict --> SimpleNamespace
D_KSTR: (pack_keystrings, unpack_datastruc, None),
D_DEC: (pack_dec, unpack_dec, 16),
D_DECS: (pack_decs, unpack_decs, 16),
D_DDICT: (pack_datastruc, unpack_datastruc_dict, None), # struc, dict --> dict
}

DATATYPE_NAMES = {
    D_BOOL: 'D_BOOL',
    D_INT8: 'D_INT8',
    D_INT16: 'D_INT16',
    D_INT32: 'D_INT32',
    D_INT64: 'D_INT64',
    D_INT128: 'D_INT128',
    D_INT8S: 'D_INT8S',
    D_INT16S: 'D_INT16S',
    D_INT32S: 'D_INT32S',
    D_INT64S: 'D_INT64S',
    D_INT128S: 'D_INT128S',
    D_STRING: 'D_STRING',
    D_JSON: 'D_JSON',
    D_RAW: 'D_RAW',
    D_RGB: 'D_RBG',
    D_DATA: 'D_DATA',
    D_KSTR: 'D_KSTR',
    D_DEC: 'D_DEC',
    D_DECS: 'D_DECS',
    D_DDICT: 'D_DDICT',
}

DATATYPE_NAMETYPES = {value:key for key,value in DATATYPE_NAMES.items()}

DATATYPE_EQ = {
    bool: D_BOOL,
    int: D_INT64S,
    str: D_STRING,
    bytes: D_RAW,
}


def unpack(datatype, data):

    return DATATYPES[datatype][DT_UNPACK](data)

def pack(datatype, data):

    return DATATYPES[datatype][DT_PACK](data)
