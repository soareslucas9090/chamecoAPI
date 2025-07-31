import requests


BLOCOS = [
    {"nome": "Bloco A"},
    {"nome": "Bloco B"},
    {"nome": "Bloco C"},
    {"nome": "Bloco D"},
    {"nome": "Bloco E"},
    {"nome": "Bloco F"},
    {"nome": "Bloco G"},
    {"nome": "Bloco H"},
    {"nome": "Bloco I"},
    {"nome": "Bloco J"},
]

SALAS = [
    {"nome": "A01 / Diretoria geral", "bloco": 1},
    {"nome": "A02 / Gabinete da diretoria geral/protocolo", "bloco": 1},
    {"nome": "A03 / Diretoria de administração e planejamento", "bloco": 1},
    {"nome": "A04 / Depto. de log. manutenção e compras/ depto. de cont. e patrimônio",
        "bloco": 1},
    {"nome": "A05 / Sala de eventos", "bloco": 1},
    {"nome": "A06 / Sala de reuniões", "bloco": 1},
    {"nome": "A07 / Copa de servidores", "bloco": 1},
    {"nome": "A08 / Psicologia", "bloco": 1},
    {"nome": "A09 / Serviço social", "bloco": 1},
    {"nome": "A10 / Tecnologia da informação", "bloco": 1},
    {"nome": "A11 / Banheiro feminino", "bloco": 1},
    {"nome": "A12 / Banheiro masculino", "bloco": 1},
    {"nome": "A13 / Coordenadoria de extensão/ SIEE/ coordenadoria de pesquisa, pós graduação e inovação",
        "bloco": 1},
    {"nome": "A14 / Setor de multimeios", "bloco": 1},
    {"nome": "A15 / Alojamentos", "bloco": 1},
    {"nome": "A16 / Alojamento masculino", "bloco": 1},
    {"nome": "A17 / Alojamento feminino", "bloco": 1},
    {"nome": "A18 / Setor de saúde", "bloco": 1},
    {"nome": "A19 / Consultório médico", "bloco": 1},
    {"nome": "A20 / Consultório de enfermagem", "bloco": 1},
    {"nome": "A21 / Esterilização", "bloco": 1},
    {"nome": "A22 / Consultorio odontologico", "bloco": 1},
    {"nome": "B01 / Coordenação de patrimonio e almoxarifado", "bloco": 2},
    {"nome": "B02 / Sala de manutenção (manutenção predial)", "bloco": 2},
    {"nome": "B03 / Deposito", "bloco": 2},
    {"nome": "B04 / Manutenção eletrica", "bloco": 2},
    {"nome": "B05 / Deposito", "bloco": 2},
    {"nome": "B06 / Vestiario de servidores", "bloco": 2},
    {"nome": "B07 / Copa dos servidores", "bloco": 2},
    {"nome": "C01 / Auditorio", "bloco": 3},
    {"nome": "Cantina", "bloco": 3},
    {"nome": "C07 / Refeitório", "bloco": 3},
    {"nome": "C11 / Rádio", "bloco": 3},
    {"nome": "D01 / Diretoria de ensino", "bloco": 4},
    {"nome": "D02 / CCA", "bloco": 4},
    {"nome": "D03 / Banheiro feminino", "bloco": 4},
    {"nome": "D04 / Banheiro masculino", "bloco": 4},
    {"nome": "D05 / Sala dos professores", "bloco": 4},
    {"nome": "D06 / Coordenação do curso de licenciatura em matemática", "bloco": 4},
    {"nome": "D07 / Coordenadoria pedagógica", "bloco": 4},
    {"nome": "D09 / Coordenação de cursos (tec. em info. e tec. em analise e desenvolvimento de sistemas)",
        "bloco": 4},
    {"nome": "D10 / Mini auditório", "bloco": 4},
    {"nome": "E01 / Deposito (lojinha)", "bloco": 5},
    {"nome": "E02 / Laboratorio de quimica", "bloco": 5},
    {"nome": "E03 / Laboratorio de fisica", "bloco": 5},
    {"nome": "E04 / Sala de aula", "bloco": 5},
    {"nome": "E05 / Sala de aula", "bloco": 5},
    {"nome": "E06 / Sala de aula", "bloco": 5},
    {"nome": "E07 / Sala de aula", "bloco": 5},
    {"nome": "E08 / Sala de aula", "bloco": 5},
    {"nome": "E09 / Sala de aula", "bloco": 5},
    {"nome": "E10 / Sala de aula", "bloco": 5},
    {"nome": "E11 / Servidor de internet (sala de internet)", "bloco": 5},
    {"nome": "E12 / Banheiro masculino", "bloco": 5},
    {"nome": "E13 / Deposito", "bloco": 5},
    {"nome": "E14 / NAPNE (coord. de cursos; tec. em info. e tec. em ads)", "bloco": 5},
    {"nome": "E15 / Setor de disciplina", "bloco": 5},
    {"nome": "E16 / Depósito", "bloco": 5},
    {"nome": "E17 / Banheiro feminino", "bloco": 5},
    {"nome": "E18 / Projeto adote uma arvore", "bloco": 5},
    {"nome": "F03 / Sala de aula", "bloco": 6},
    {"nome": "F04 / Sala de aula", "bloco": 6},
    {"nome": "F05 / Laboratorio de soldas", "bloco": 6},
    {"nome": "F06 / Sala de aula", "bloco": 6},
    {"nome": "F07 / Laboratorio de desenho", "bloco": 6},
    {"nome": "F08 / Laboratorio de automacao", "bloco": 6},
    {"nome": "F09 / Laboratorio de eletricidade", "bloco": 6},
    {"nome": "F10 / Laboratorio de metrologia", "bloco": 6},
    {"nome": "F11 / Banheiro masculino", "bloco": 6},
    {"nome": "F12 / Deposito", "bloco": 6},
    {"nome": "F13 / Coordenação de biologia", "bloco": 6},
    {"nome": "F14 / Coordenação de cursos(tecnico em eletromecanica e tecnico em meio ambiente)",
        "bloco": 6},
    {"nome": "F15 / Depósito", "bloco": 6},
    {"nome": "F16 / Banheiro feminino", "bloco": 6},
    {"nome": "G01 / Sala de manutenção de informática", "bloco": 7},
    {"nome": "G02 / Laboratório de informática 3", "bloco": 7},
    {"nome": "G03 / Laboratório de informática 2", "bloco": 7},
    {"nome": "G04 / Laboratório de informática 1", "bloco": 7},
    {"nome": "G05 / Laboratório de materiais de construção/ coord. Do curso técnico em edificações",
        "bloco": 7},
    {"nome": "G06 / Sala de professores", "bloco": 7},
    {"nome": "G07 / Almoxarifado", "bloco": 7},

    {"nome": "G08 / Biblioteca", "bloco": 7},
    {"nome": "G17 / LIFE", "bloco": 7},
    {"nome": "G18 / Laboratório de ensino de biologia", "bloco": 7},
    {"nome": "G19 / Laboratório de biologia", "bloco": 7},
    {"nome": "G23 / Laboratório de instalações domiciliares", "bloco": 7},
    {"nome": "G23 / Depósito", "bloco": 7},
    {"nome": "G24 / Manutenção de tec. Da informação", "bloco": 7},
    {"nome": "G25 / Depósito", "bloco": 7},
    {"nome": "G26 / Coordenação de matemática", "bloco": 7},
    {"nome": "G27 / Grêmio de representação estudantil", "bloco": 7},
    {"nome": "G28 / Depósito", "bloco": 7},
    {"nome": "G29 / Manutenção de tec. Da informação", "bloco": 7},
    {"nome": "Laboratório de ensino biologia", "bloco": 7},
    {"nome": "H02 / Salas de jogos", "bloco": 8},
    {"nome": "H03 / Sala de lutas", "bloco": 8},
    {"nome": "H04 / Academia", "bloco": 8},
    {"nome": "H11 / Vestiário feminino", "bloco": 8},
    {"nome": "H10 / Vestiário masculino", "bloco": 8},
    {"nome": "Quadra poliesportiva", "bloco": 8},
    {"nome": "Almoxarifado", "bloco": 8},
    {"nome": "H06 / Setor de educação física", "bloco": 8},
    {"nome": "H08 / Depósito", "bloco": 8},
    {"nome": "H09 / Banheiro masculino", "bloco": 8},
    {"nome": "I03 / Arquivo", "bloco": 9},
    {"nome": "I02 / Banheiro", "bloco": 9},
    {"nome": "I04 / Depósito", "bloco": 9},
    {"nome": "J18 / Laboratório de informática", "bloco": 10},
    {"nome": "J17 / Laboratório de informática", "bloco": 10},
    {"nome": "J16 / Setor de disciplina", "bloco": 10},
    {"nome": "J15 / Sala de professores", "bloco": 10},
    {"nome": "J01 / Sala de professores atendimento", "bloco": 10},
    {"nome": "J14 / Banheiro feminino", "bloco": 10},
    {"nome": "J13 / Banheiro feminino para deficiente", "bloco": 10},
    {"nome": "J12 / Banheiro masculino para deficiente", "bloco": 10},
    {"nome": "J02 / Sala de aula", "bloco": 10},
    {"nome": "J11 / Banheiro masculino", "bloco": 10},
    {"nome": "J10 / Arquivo", "bloco": 10},
    {"nome": "J03 / Sala de aula", "bloco": 10},
    {"nome": "J04 / Sala de aula", "bloco": 10},
    {"nome": "J05 / Sala de aula", "bloco": 10},
    {"nome": "J06 / Sala de aula", "bloco": 10},
    {"nome": "J07 / Sala de aula", "bloco": 10},
    {"nome": "J08 / Sala de aula", "bloco": 10},
    {"nome": "J09 / Sala de aula", "bloco": 10},
]

# troca a url pela correta da API
API_URL = "http://localhost:8000/chameco/api/v1/"
# coloque um token válido
TOKEN = "de00f474696a36544bc2964c719f10f8bee1e8ff2f16eb7287aa1e52803d7d55"


def inserir_blocos():
    bloco_id_map = {}
    for bloco in BLOCOS:
        data = bloco.copy()
        data["token"] = TOKEN
        resp = requests.post(f"{API_URL}blocos/", json=data)
        if resp.status_code == 201:
            bloco_id = resp.json()["id"]
            bloco_id_map[bloco["nome"]] = bloco_id
            print(f"Bloco '{bloco['nome']}' inserido (id={bloco_id})")
        else:
            print(f"Erro ao inserir bloco '{bloco['nome']}':", resp.text)
    return bloco_id_map


def inserir_salas(bloco_id_map):
    sala_id_map = {}
    for sala in SALAS:
        data = {
            "nome": sala["nome"],
            "bloco": sala["bloco"],
            "token": TOKEN,
        }
        resp = requests.post(f"{API_URL}salas/", json=data)
        if resp.status_code == 201:
            sala_id = resp.json()["id"]
            sala_id_map[sala["nome"]] = sala_id
            print(f"Sala '{sala['nome']}' inserida (id={sala_id})")
        else:
            print(f"Erro ao inserir sala '{sala['nome']}':", resp.text)
    return sala_id_map


def inserir_chaves():
    for i in range(1, len(SALAS)):
        data = {
            "sala": i,
            "disponivel": True,
            "principal": True,
            "descricao": f"Chave principal da sala {SALAS[i-1]["nome"]}",
            "token": TOKEN,
        }
        resp = requests.post(f"{API_URL}chaves/", json=data)
        if resp.status_code == 201:
            print(
                f"Chave inserida")
        else:
            print(
                f"Erro ao inserir chave")


if __name__ == "__main__":
    print("Inserindo blocos...")
    blocos = inserir_blocos()
    print("Inserindo salas...")
    salas = inserir_salas(blocos)
    print("Inserindo chaves...")
    inserir_chaves()
    print("Processo finalizado.")
