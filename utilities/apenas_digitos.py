def apenas_digitos(string):

    digitos = ""

    for d in string:
        if d.isdigit():
            digitos += d

    return digitos
    