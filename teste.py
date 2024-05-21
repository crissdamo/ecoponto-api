
def agrupar_horarios(dia_funcionamento):
    from collections import defaultdict
    import itertools

    # Passo 1: Organizar horários por dia da semana
    horarios_por_dia = defaultdict(list)
    for horario in dia_funcionamento:
        dia = horario['dia_semana']
        intervalo = f"{horario['hora_inicial']} às {horario['hora_final']}"
        horarios_por_dia[dia].append(intervalo)

    # Passo 2: Identificar horários iguais em dias consecutivos
    dias_semana = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    grupos = []
    for key, group in itertools.groupby(enumerate(dias_semana), lambda x: horarios_por_dia.get(x[1])):
        dias_grupo = list(group)
        if key:  # Apenas adiciona se key não for None
            grupos.append((key, [dias[1] for dias in dias_grupo]))

    # Passo 3: Criar a string resumida
    partes = []

    for horarios, dias in grupos:
        dias_str = dias[0] if len(dias) == 1 else f"{dias[0]} a {dias[-1]}"
        horarios_str = " - ".join(horarios_por_dia[dias[0]])
        partes.append(f"{dias_str} das {horarios_str}")


    funcionamento_string = ""
    len_partes = len(partes) - 1
    for index, parte in enumerate(partes):
        
        # ultimo ou só tem um
        if index == len_partes or len_partes == 0:
            funcionamento_string += f"{parte} "
        
        # penúltimo
        elif (len_partes - index) == 1:
            funcionamento_string += f"{parte} e "

        else:
            funcionamento_string += f"{parte}, "
        
    return funcionamento_string

# Dados de entrada
dia_funcionamento = [
    {"dia_semana": "seg", "hora_inicial": "10:00", "hora_final": "11:30"},
    # {"dia_semana": "seg", "hora_inicial": "13:00", "hora_final": "18:00"},
    {"dia_semana": "ter", "hora_inicial": "09:00", "hora_final": "11:30"},
    {"dia_semana": "ter", "hora_inicial": "14:00", "hora_final": "18:00"},
    {"dia_semana": "qua", "hora_inicial": "09:00", "hora_final": "11:30"},
    {"dia_semana": "qua", "hora_inicial": "14:00", "hora_final": "18:00"},
    {"dia_semana": "qui", "hora_inicial": "10:00", "hora_final": "11:30"},
    {"dia_semana": "qui", "hora_inicial": "13:00", "hora_final": "18:00"},
    {"dia_semana": "sex", "hora_inicial": "10:00", "hora_final": "11:30"},
    {"dia_semana": "sex", "hora_inicial": "13:00", "hora_final": "18:00"}
]

# Executar a função e imprimir o resultado
resultado = agrupar_horarios(dia_funcionamento)
print(resultado)