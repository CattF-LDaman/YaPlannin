from types import SimpleNamespace

from YaP.YaPCore.Data.datatypes import pack, unpack, DATATYPES, DT_SIZE

_FIELD_NAME = 0
_FIELD_DATATYPE = 1
_FIELD_DATATYPE_LENSIZE = 2 # only for varied-size datatypes eg. D_STRING

def build_struc(struc, struc_data):
    """
    Packs structured data into bytes according to the provided structure definition.

    Parameters:
        struc (list): List of field definitions. Each field is a list/tuple containing:
            - field name (str)
            - field datatype (int, as defined in DATATYPES)
            - (optional) length size (int), only for variable-length datatypes
        struc_data (dict): Dictionary mapping field names to their values.

    Returns:
        bytes: The packed byte representation of the structured data.
    """
    struc_packed = b""
    for field in struc:

        field_data = struc_data[field[_FIELD_NAME]]
        try:
            field_data_packed = pack(field[_FIELD_DATATYPE], field_data)
        except Exception as e:
            raise type(e)(f"{field[_FIELD_NAME]}: {str(e)}")

        if DATATYPES[field[_FIELD_DATATYPE]][DT_SIZE] is None:

            field_len = len(field_data_packed)
            field_len_packed = field_len.to_bytes(field[_FIELD_DATATYPE_LENSIZE], "little")
            field_packed = field_len_packed + field_data_packed

        else:

            field_packed = field_data_packed

        struc_packed += field_packed

    return struc_packed

def read_struc(struc, struc_data, namespace=True):
    """
    Unpacks bytes into structured data according to the provided structure definition.

    Parameters:
        struc (list): List of field definitions. Each field is a list/tuple containing:
            - field name (str)
            - field datatype (int, as defined in DATATYPES)
            - (optional) length size (int), only for variable-length datatypes
        struc_data (bytes): The packed byte data to unpack.
        namespace (bool): If True, returns a SimpleNamespace; otherwise, returns a dict.

    Returns:
        SimpleNamespace or dict: The unpacked structured data.
    """
    packet_out = {}

    cur_index = 0
    for field in struc:

        if DATATYPES[field[_FIELD_DATATYPE]][DT_SIZE] is None:

            field_len = int.from_bytes(struc_data[cur_index:cur_index+field[_FIELD_DATATYPE_LENSIZE]], "little")
            cur_index+=field[_FIELD_DATATYPE_LENSIZE]

        else:

            field_len = DATATYPES[field[_FIELD_DATATYPE]][DT_SIZE]

        field_data_packed = struc_data[cur_index:cur_index+field_len]
        field_data = unpack(field[_FIELD_DATATYPE],field_data_packed)

        packet_out[field[_FIELD_NAME]] = field_data

        cur_index += field_len

    return SimpleNamespace(**packet_out) if namespace else packet_out
