import re

def validar_email(email):
    # Expressão regular para validar o formato do e-mail
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Verificar se o e-mail corresponde ao padrão
    if re.match(regex, email):
        return True
    else:
        return False
    