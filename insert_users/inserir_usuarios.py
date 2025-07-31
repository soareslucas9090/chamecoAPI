import requests
import openpyxl
import re


API_URL = "http://localhost:8000/chameco/api/v1/"


def ler_xlsx_para_dicionario(caminho_arquivo):
    workbook = openpyxl.load_workbook(caminho_arquivo)
    sheet = workbook.active

    cabecalhos = [cell.value for cell in sheet[1]]

    dados = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if all(cell is None for cell in row):
            continue

        linha_dict = {cabecalhos[i]: row[i] for i in range(len(cabecalhos))}
        dados.append(linha_dict)

    return dados


def main():
    caminho_arquivo = "insert_users/alunos.xlsx"
    dados_alunos = ler_xlsx_para_dicionario(caminho_arquivo)

    for linha in dados_alunos:
        data = {
            'cpf': re.sub("[^0-9]", "", linha["CPF"]),
            'password': linha["Matrícula"].lower()
        }

        resp = requests.post(f"{API_URL}login/", json=data)

        if resp.status_code == 200:
            print(
                f"Usuário '{resp.json()["nome"]}' inserido (usuario={resp.json()["usuario"]})")
        else:
            print(
                f"Erro no usuário de CPF: {re.sub("[^0-9]", "", linha["CPF"])}, matricula: {linha['Matrícula'].lower()}, mensagem: {resp.text}")

    caminho_arquivo = "insert_users/servidores.xlsx"
    dados_servidores = ler_xlsx_para_dicionario(caminho_arquivo)

    for linha in dados_servidores:
        try:
            cpf = str(re.sub("[^0-9]", "", linha["Matrícula"])).lower()
        except:
            cpf = linha["Matrícula"]

        data = {
            'cpf': cpf,
            'password': cpf
        }

        resp = requests.post(f"{API_URL}login/", json=data)

        if resp.status_code == 200:
            print(
                f"Usuário '{resp.json()["nome"]}' inserido (usuario={resp.json()["usuario"]})")
        else:
            print(
                f"Erro no usuário de Matrícula: {linha['Matrícula'].lower()}: {resp.text}")

    caminho_arquivo = "insert_users/terceirizados.xlsx"
    dados_terceirizados = ler_xlsx_para_dicionario(caminho_arquivo)

    for linha in dados_terceirizados:
        try:
            cpf = re.sub("[^0-9]", "", str(linha["CPF"]))
        except:
            cpf = re.sub("[^0-9]", "", linha["CPF"])

        data = {
            'cpf': cpf,
            'password': cpf
        }

        resp = requests.post(f"{API_URL}login/", json=data)

        if resp.status_code == 200:
            print(
                f"Usuário '{resp.json()["nome"]}' inserido (usuario={resp.json()["usuario"]})")
        else:
            print(
                f"Erro no usuário de CPF: {re.sub("[^0-9]", "", linha["CPF"])}: {resp.text}")


if __name__ == "__main__":
    main()
