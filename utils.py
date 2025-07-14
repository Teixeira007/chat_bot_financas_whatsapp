def parse_add_comando(mensagem):
    """
    Formato esperado: add categoria descrição valor
    Exemplo: add transporte uber 37,90
    """
    partes = mensagem.strip().split()
    if len(partes) < 4:
        return None

    if partes[0].lower() != "add":
        return None

    categoria = partes[1]
    valor_str = partes[-1].replace(",", ".")
    try:
        valor = float(valor_str)
    except ValueError:
        return None

    descricao = " ".join(partes[2:-1])
    return categoria.lower(), descricao, valor
