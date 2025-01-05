source = ""
localTarget = ""
remoteTarget=""
items = []
necessaryFiles =  ['.xml', 'camera-1.raw16', 'left.wav', 'right.wav']
logLocation = "log.txt"

def digest(f):
    import hashlib

    md5 = hashlib.md5()
    with open(f,'rb') as fv:
        for chunk in iter(lambda: fv.read(128*md5.block_size), ''):
            md5.update(chunk)
    return md5.hexdigest()
