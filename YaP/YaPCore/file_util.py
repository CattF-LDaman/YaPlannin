import hashlib

def format_n_bytes(size):
    power = 2**10
    n = 0
    units = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"

def get_file_hash(path, algo='sha256', chunk_size=65536):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()
