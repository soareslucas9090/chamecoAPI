from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from .models import (
	Blocos,
	Chaves,
	Emprestimos,
	PessoasAutorizadas,
	Salas,
	Usuarios,
	UsuariosResponsaveis,
)


class ViewSetGetAndRetrieveTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.bloco_academico = Blocos.objects.create(nome="Prédio Acadêmico")
		cls.bloco_biblioteca = Blocos.objects.create(nome="Biblioteca Central")

		cls.sala_joao = Salas.objects.create(
			nome="Sala João",
			bloco=cls.bloco_academico,
		)
		cls.sala_auditorio = Salas.objects.create(
			nome="Auditório Principal",
			bloco=cls.bloco_biblioteca,
		)

		cls.usuario_joao = Usuarios.objects.create(
			nome="João da Silva",
			id_cortex=101,
			setor="Direção de Ensino",
			tipo="Técnico Administrativo",
			email="joao@example.com",
		)
		cls.usuario_maria = Usuarios.objects.create(
			nome="Maria de Souza",
			id_cortex=102,
			setor="Coordenação de Informática",
			tipo="Professor",
			email="maria@example.com",
		)
		cls.usuario_carlos = Usuarios.objects.create(
			nome="Carlos Oliveira",
			id_cortex=103,
			setor="Biblioteca",
			tipo="Servidor",
			email="carlos@example.com",
		)

		PessoasAutorizadas.objects.create(usuario=cls.usuario_joao, sala=cls.sala_joao)
		PessoasAutorizadas.objects.create(usuario=cls.usuario_maria, sala=cls.sala_auditorio)

		cls.responsavel_financeiro = UsuariosResponsaveis.objects.create(
			nome="Responsável Financeiro",
			superusuario=cls.usuario_joao,
		)
		cls.responsavel_academico = UsuariosResponsaveis.objects.create(
			nome="Responsável Acadêmico",
			superusuario=cls.usuario_maria,
		)

		cls.chave_joao = Chaves.objects.create(
			sala=cls.sala_joao,
			disponivel=True,
			principal=True,
			descricao="Chave principal da sala João",
		)
		cls.chave_auditorio = Chaves.objects.create(
			sala=cls.sala_auditorio,
			disponivel=False,
			principal=False,
			descricao="Chave reserva do auditório",
		)

		cls.emprestimo_aberto = Emprestimos.objects.create(
			chave=cls.chave_joao,
			usuario_solicitante=cls.usuario_joao,
			usuario_responsavel=cls.responsavel_financeiro,
			observacao="Empréstimo em andamento",
		)
		cls.emprestimo_fechado = Emprestimos.objects.create(
			chave=cls.chave_auditorio,
			usuario_solicitante=cls.usuario_maria,
			usuario_responsavel=cls.responsavel_academico,
			observacao="Empréstimo finalizado",
		)

		known_day = timezone.now() - timedelta(days=2)
		Emprestimos.objects.filter(pk=cls.emprestimo_aberto.pk).update(
			horario_emprestimo=known_day,
		)
		Emprestimos.objects.filter(pk=cls.emprestimo_fechado.pk).update(
			horario_emprestimo=known_day,
			horario_devolucao=known_day + timedelta(hours=3),
		)

		cls.emprestimo_aberto.refresh_from_db()
		cls.emprestimo_fechado.refresh_from_db()

	def setUp(self):
		self.token = "token-teste"

	def _get(self, path, params=None):
		params = params or {}
		params.setdefault("token", self.token)
		return self.client.get(path, params)

	def _assert_list_ids(self, response, expected_ids):
		self.assertEqual(response.status_code, 200)
		self.assertIn("results", response.data)
		self.assertEqual(
			[item["id"] for item in response.data["results"]],
			expected_ids,
		)

	@patch("chamecoapi.permissions.isTokenValid", return_value=True)
	def test_usuarios_list_and_retrieve(self, mocked_token):
		base_path = "/chameco/api/v1/usuarios/"

		response = self._get(base_path)
		self._assert_list_ids(
			response,
			[self.usuario_joao.id, self.usuario_maria.id, self.usuario_carlos.id],
		)

		search_cases = [
			({"nome": "JOAO"}, [self.usuario_joao.id]),
			({"nome": "Silv"}, [self.usuario_joao.id]),
			({"tipo": "tecnico"}, [self.usuario_joao.id]),
			({"setor": "direcao de ensino"}, [self.usuario_joao.id]),
			({"setor": "INFORMATICA"}, [self.usuario_maria.id]),
		]

		for params, expected_ids in search_cases:
			with self.subTest(params=params):
				response = self._get(base_path, params)
				self._assert_list_ids(response, expected_ids)

		response = self._get(f"{base_path}{self.usuario_maria.id}/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], self.usuario_maria.id)
		self.assertEqual(response.data["nome"], self.usuario_maria.nome)
		self.assertEqual(response.data["tipo"], self.usuario_maria.tipo)

	@patch("chamecoapi.permissions.isTokenValid", return_value=True)
	def test_blocos_list_and_retrieve(self, mocked_token):
		base_path = "/chameco/api/v1/blocos/"

		response = self._get(base_path)
		self._assert_list_ids(
			response,
			[self.bloco_biblioteca.id, self.bloco_academico.id],
		)

		search_cases = [
			({"nome": "predio"}, [self.bloco_academico.id]),
			({"nome": "PREDIO ACAD"}, [self.bloco_academico.id]),
			({"nome": "bibliot"}, [self.bloco_biblioteca.id]),
		]

		for params, expected_ids in search_cases:
			with self.subTest(params=params):
				response = self._get(base_path, params)
				self._assert_list_ids(response, expected_ids)

		response = self._get(f"{base_path}{self.bloco_academico.id}/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], self.bloco_academico.id)
		self.assertEqual(response.data["nome"], self.bloco_academico.nome)

	@patch("chamecoapi.permissions.isTokenValid", return_value=True)
	def test_salas_list_and_retrieve(self, mocked_token):
		base_path = "/chameco/api/v1/salas/"

		response = self._get(base_path)
		self._assert_list_ids(
			response,
			[self.sala_auditorio.id, self.sala_joao.id],
		)

		search_cases = [
			({"nome": "auditorio"}, [self.sala_auditorio.id]),
			({"nome": "SALA JO"}, [self.sala_joao.id]),
			({"bloco": "predio"}, [self.sala_joao.id]),
			({"bloco": "biblioteca"}, [self.sala_auditorio.id]),
		]

		for params, expected_ids in search_cases:
			with self.subTest(params=params):
				response = self._get(base_path, params)
				self._assert_list_ids(response, expected_ids)

		response = self._get(f"{base_path}{self.sala_auditorio.id}/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], self.sala_auditorio.id)
		self.assertEqual(response.data["nome"], self.sala_auditorio.nome)
		self.assertEqual(response.data["nome_bloco"], self.bloco_biblioteca.nome)

	@patch("chamecoapi.permissions.isTokenValid", return_value=True)
	def test_chaves_list_and_retrieve(self, mocked_token):
		base_path = "/chameco/api/v1/chaves/"

		response = self._get(base_path)
		self._assert_list_ids(
			response,
			[self.chave_joao.id, self.chave_auditorio.id],
		)

		search_cases = [
			({"sala": "joao"}, [self.chave_joao.id]),
			({"sala": "AUDITORIO"}, [self.chave_auditorio.id]),
			({"bloco": "predio"}, [self.chave_joao.id]),
			({"bloco": "biblioteca"}, [self.chave_auditorio.id]),
			({"disponivel": "true"}, [self.chave_joao.id]),
			({"disponivel": "false"}, [self.chave_auditorio.id]),
		]

		for params, expected_ids in search_cases:
			with self.subTest(params=params):
				response = self._get(base_path, params)
				self._assert_list_ids(response, expected_ids)

		response = self._get(f"{base_path}{self.chave_auditorio.id}/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], self.chave_auditorio.id)
		self.assertEqual(response.data["sala"], self.sala_auditorio.id)
		self.assertEqual(response.data["disponivel"], self.chave_auditorio.disponivel)

	@patch("chamecoapi.permissions.isTokenValid", return_value=True)
	def test_responsaveis_list_and_retrieve(self, mocked_token):
		base_path = "/chameco/api/v1/responsaveis/"

		response = self._get(base_path)
		self._assert_list_ids(
			response,
			[self.responsavel_academico.id, self.responsavel_financeiro.id],
		)

		search_cases = [
			({"nome_superusuario": "joao"}, [self.responsavel_financeiro.id]),
			({"nome_superusuario": "MARI"}, [self.responsavel_academico.id]),
			({"superusuario": str(self.usuario_joao.id)}, [self.responsavel_financeiro.id]),
			({"nome": "finance"}, [self.responsavel_financeiro.id]),
			({"nome": "ACAD"}, [self.responsavel_academico.id]),
		]

		for params, expected_ids in search_cases:
			with self.subTest(params=params):
				response = self._get(base_path, params)
				self._assert_list_ids(response, expected_ids)

		response = self._get(f"{base_path}{self.responsavel_financeiro.id}/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], self.responsavel_financeiro.id)
		self.assertEqual(response.data["nome"], self.responsavel_financeiro.nome)
		self.assertEqual(
			response.data["superusuario"], self.usuario_joao.id,
		)

	@patch("chamecoapi.permissions.isTokenValid", return_value=True)
	def test_emprestimos_list_and_retrieve(self, mocked_token):
		base_path = "/chameco/api/v1/emprestimos/"

		response = self._get(base_path)
		self._assert_list_ids(
			response,
			[self.emprestimo_fechado.id, self.emprestimo_aberto.id],
		)

		search_cases = [
			({"data": timezone.localdate(self.emprestimo_aberto.horario_emprestimo).isoformat()}, [self.emprestimo_fechado.id, self.emprestimo_aberto.id]),
			({"solicitante": "joao"}, [self.emprestimo_aberto.id]),
			({"solicitante": "mari"}, [self.emprestimo_fechado.id]),
			({"responsavel": "finance"}, [self.emprestimo_aberto.id]),
			({"responsavel": "acad"}, [self.emprestimo_fechado.id]),
			({"finalizados": "true"}, [self.emprestimo_fechado.id]),
			({"finalizados": "false"}, [self.emprestimo_aberto.id]),
		]

		for params, expected_ids in search_cases:
			with self.subTest(params=params):
				response = self._get(base_path, params)
				self._assert_list_ids(response, expected_ids)

		response = self._get(f"{base_path}{self.emprestimo_fechado.id}/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], self.emprestimo_fechado.id)
		self.assertEqual(response.data["chave"], self.chave_auditorio.id)
		self.assertEqual(
			response.data["usuario_solicitante"], self.usuario_maria.id,
		)
		self.assertEqual(
			response.data["usuario_responsavel"], self.responsavel_academico.id,
		)
