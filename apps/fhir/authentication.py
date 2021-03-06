import base64


def extract_username(auth, auth_prefix="SLS"):
    splitted = auth.split(" ", 1)
    if len(splitted) != 2:
        return None
    auth_type, auth_string = splitted

    if auth_type != auth_prefix:
        return None

    encoding = "utf-8"

    # raises (TypeError, binascii.Error)
    b64_decoded = base64.b64decode(auth_string)

    # raises UnicodeDecodeError
    auth_string_decoded = b64_decoded.decode(encoding)

    return convert_sls_uuid(auth_string_decoded)


def convert_sls_uuid(id):
    # Do not shorten SLS guid. It causes username collisions
    # return id[9:36]
    return id
