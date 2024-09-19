class Funcionario:

    def __init__(self, nome, autorizacao):
        self.nome = nome
        self.autorizacao = autorizacao
        self.horarios = []

    def registrar_entrada(self, hora):
        self.horarios.append(hora)

    def __str__(self):
        return f"{self.nome} (Autorizado: {self.autorizacao})"
