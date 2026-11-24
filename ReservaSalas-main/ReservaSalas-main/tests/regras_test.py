import unittest
from datetime import datetime
from types import SimpleNamespace

from reservaSalas.regras.regras import avaliar_reserva, intervalos_sobrepoem, validar_intervalo

AGORA = datetime(2026, 11, 23, 9, 0)

def hora(dia, h, m=0):
    return datetime(2026, 11, dia, h, m)

def reserva(inicio, fim, situacao="CONFIRMADA"):
    return SimpleNamespace(data_hora_inicio=inicio, data_hora_fim=fim, situacao=situacao)

SALA = SimpleNamespace(capacidade=4, recursos=["Quadro branco"])

def proposta(inicio, fim, grupo=3, recursos=()):
    return {"inicio": inicio, "fim": fim, "grupo": grupo, "recursos": list(recursos)}

class ValidarIntervaloTest(unittest.TestCase):
    def test_reserva_valida(self):
        self.assertIsNone(validar_intervalo(hora(24, 10), hora(24, 11, 30), "RESERVA", AGORA))

    def test_inicio_depois_do_fim(self):
        self.assertEqual(validar_intervalo(hora(24, 11), hora(24, 10), "RESERVA", AGORA), "INTERVALO_INVALIDO")

    def test_minuto_quebrado(self):
        self.assertEqual(validar_intervalo(hora(24, 10, 15), hora(24, 11, 15), "RESERVA", AGORA), "HORARIO_INVALIDO")

    def test_antes_das_8_e_depois_das_22(self):
        self.assertEqual(validar_intervalo(hora(24, 7, 30), hora(24, 8, 30), "RESERVA", AGORA), "HORARIO_INVALIDO")
        self.assertEqual(validar_intervalo(hora(24, 21, 30), hora(24, 22, 30), "RESERVA", AGORA), "HORARIO_INVALIDO")

    def test_termina_exatamente_as_22(self):
        self.assertIsNone(validar_intervalo(hora(24, 21), hora(24, 22), "RESERVA", AGORA))

    def test_duracao(self):
        self.assertEqual(validar_intervalo(hora(24, 10), hora(24, 12, 30), "RESERVA", AGORA), "DURACAO_INVALIDA")
        self.assertIsNone(validar_intervalo(hora(24, 10), hora(24, 12), "RESERVA", AGORA))

    def test_antecedencia(self):
        self.assertEqual(validar_intervalo(hora(23, 9), hora(23, 10), "RESERVA", AGORA), "ANTECEDENCIA_INVALIDA")
        self.assertIsNone(validar_intervalo(hora(30, 9), hora(30, 10), "RESERVA", AGORA))
        self.assertEqual(validar_intervalo(hora(30, 9, 30), hora(30, 10, 30), "RESERVA", AGORA), "ANTECEDENCIA_INVALIDA")

    def test_bloqueio_pode_atravessar_dias(self):
        self.assertIsNone(validar_intervalo(hora(24, 8), hora(26, 22), "BLOQUEIO", AGORA))

    def test_bloqueio_no_passado(self):
        self.assertEqual(validar_intervalo(hora(22, 8), hora(24, 8), "BLOQUEIO", AGORA), "ANTECEDENCIA_INVALIDA")


class AvaliarReservaTest(unittest.TestCase):
    def test_sobreposicao_exclui_o_fim(self):
        # 10h-11h não conflita com 11h-12h (RN05)
        self.assertFalse(intervalos_sobrepoem(hora(24, 10), hora(24, 11), hora(24, 11), hora(24, 12)))
        self.assertTrue(intervalos_sobrepoem(hora(24, 10), hora(24, 11), hora(24, 10, 30), hora(24, 12)))

    def test_valida(self):
        self.assertIsNone(avaliar_reserva(proposta(hora(24, 10), hora(24, 11)), SALA, [], [], [], AGORA))

    def test_grupo_pequeno_e_capacidade(self):
        self.assertEqual(avaliar_reserva(proposta(hora(24, 10), hora(24, 11), grupo=1), SALA, [], [], [], AGORA), "DADOS_INVALIDOS")
        self.assertEqual(avaliar_reserva(proposta(hora(24, 10), hora(24, 11), grupo=5), SALA, [], [], [], AGORA), "CAPACIDADE_EXCEDIDA")

    def test_recurso(self):
        self.assertEqual(avaliar_reserva(proposta(hora(24, 10), hora(24, 11), recursos=["TV"]), SALA, [], [], [], AGORA), "RECURSO_INDISPONIVEL")

    def test_limite_pessoal(self):
        minhas = [reserva(hora(25, 10), hora(25, 11)), reserva(hora(26, 10), hora(26, 11))]
        self.assertEqual(avaliar_reserva(proposta(hora(24, 10), hora(24, 11)), SALA, minhas, [], [], AGORA), "LIMITE_ATINGIDO")

    def test_canceladas_nao_contam_no_limite(self):
        minhas = [reserva(hora(25, 10), hora(25, 11), "CANCELADA"), reserva(hora(26, 10), hora(26, 11))]
        self.assertIsNone(avaliar_reserva(proposta(hora(24, 10), hora(24, 11)), SALA, minhas, [], [], AGORA))

    def test_conflito_estudante(self):
        minhas = [reserva(hora(24, 10, 30), hora(24, 11, 30))]
        self.assertEqual(avaliar_reserva(proposta(hora(24, 10), hora(24, 11)), SALA, minhas, [], [], AGORA), "CONFLITO_ESTUDANTE")

    def test_conflito_sala(self):
        da_sala = [reserva(hora(24, 10, 30), hora(24, 11, 30))]
        self.assertEqual(avaliar_reserva(proposta(hora(24, 10), hora(24, 11)), SALA, [], da_sala, [], AGORA), "CONFLITO_SALA")

    def test_sala_bloqueada(self):
        bloqueio = SimpleNamespace(data_hora_inicio=hora(24, 8), data_hora_fim=hora(24, 22), situacao="ATIVO")
        self.assertEqual(avaliar_reserva(proposta(hora(24, 10), hora(24, 11)), SALA, [], [], [bloqueio], AGORA), "SALA_BLOQUEADA")
        bloqueio.situacao = "CANCELADO"
        self.assertIsNone(avaliar_reserva(proposta(hora(24, 10), hora(24, 11)), SALA, [], [], [bloqueio], AGORA))


if __name__ == "__main__":
    unittest.main()