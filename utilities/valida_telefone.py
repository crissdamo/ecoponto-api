def validar_telefone(telefone):

    digitos = ""

    for d in telefone:
        if d.isdigit():
            digitos += d

    if len(digitos) < 10 or len(digitos) > 14:
        return False
    return True
    