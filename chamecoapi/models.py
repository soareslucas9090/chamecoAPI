from django.db import models


class Usuarios(models.Model):
    nome = models.CharField(null=False)
    id_cortex = models.IntegerField(null=False, unique=True)
    setor = models.CharField(null=False)
    tipo = models.CharField(null=False)
    chaves_autorizadas = models.ManyToManyField("Chaves", through="PessoasAutorizadas")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        str = f"{self.nome}"
        return str


class Blocos(models.Model):
    nome = models.CharField(max_length=128, null=False)

    class Meta:
        verbose_name = "Bloco"
        verbose_name_plural = "Blocos"

    def __str__(self) -> str:
        str = f"{self.nome}"
        return str


class Salas(models.Model):
    nome = models.CharField(max_length=128, null=False)
    bloco = models.ForeignKey(
        Blocos, related_name="salas", on_delete=models.CASCADE, null=False
    )

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"

    def __str__(self) -> str:
        str = f"{self.nome}"
        return str


class Chaves(models.Model):
    sala = models.OneToOneField(
        Salas, related_name="chave", on_delete=models.CASCADE, null=False
    )
    disponivel = models.BooleanField(default=True, null=False)
    usuarios_autorizados = models.ManyToManyField(
        Usuarios, through="PessoasAutorizadas"
    )

    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"

    def __str__(self) -> str:
        str = f"Chave da sala {self.sala.nome}"
        return str


class PessoasAutorizadas(models.Model):
    usuario = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        null=False,
    )
    chave = models.ForeignKey(
        Chaves,
        on_delete=models.CASCADE,
        null=False,
    )

    def __str__(self) -> str:
        str = f"Usuario: {self.usuario}, chave: {self.chave}"
        return str


class Emprestimos(models.Model):
    horario_emprestimo = models.DateTimeField(auto_now_add=True)
    horario_devolucao = models.DateTimeField(null=True)
    chave = models.ForeignKey(
        Chaves,
        related_name="emprestimos_de_chaves",
        on_delete=models.CASCADE,
        null=False,
    )
    usuario_responsavel = models.ForeignKey(
        Usuarios,
        related_name="emprestimos_responsaveis",
        on_delete=models.CASCADE,
        null=False,
    )
    usuario_solicitante = models.ForeignKey(
        Usuarios,
        related_name="emprestimos_solicitados",
        on_delete=models.CASCADE,
        null=False,
    )

    class Meta:
        verbose_name = "Emprestimo"
        verbose_name_plural = "Emprestimos"

    def __str__(self) -> str:
        str = f"Horario: {self.horario_emprestimo}, chave: {self.chave}"
        return str
