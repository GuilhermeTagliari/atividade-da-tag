import RPi.GPIO as GPIO
import time
import csv
from mfrc522 import SimpleMFRC522
from funcionaario import Funcionario

GPIO.setmode(GPIO.BOARD)

LED_VERDE_PIN = 12
LED_VERMELHO_PIN = 8
BUZZER_PIN = 10

GPIO.setup(LED_VERDE_PIN, GPIO.OUT)
GPIO.setup(LED_VERMELHO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)


GPIO.output(LED_VERDE_PIN, GPIO.LOW)
GPIO.output(LED_VERMELHO_PIN, GPIO.LOW)

buzzer_pwm = GPIO.PWM(BUZZER_PIN, 440)

reader = SimpleMFRC522()


funcionarios = {
    '771439528262': Funcionario("João Guilherme", True),
    '761383686137': Funcionario("Maria Silva", False),
}

entrada_colaboradores = {}
tempo_permanencia = {}

tentativas_nao_autorizadas = {}
tentativas_invasao = 0

# Função para tocar o buzzer
def tocar_buzzer(frequencia, duracao):
    buzzer_pwm.ChangeFrequency(frequencia)
    buzzer_pwm.start(50)
    time.sleep(duracao)
    buzzer_pwm.stop()

# Função para acender o LED
def acender_led(pin, duracao):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duracao)
    GPIO.output(pin, GPIO.LOW)

# Função para piscar o LED com o buzzer
def piscar_led_com_buzzer(pin_led, frequencia_buzzer, num_piscadas, intervalo):
    for _ in range(num_piscadas):
        GPIO.output(pin_led, GPIO.HIGH)
        buzzer_pwm.ChangeFrequency(frequencia_buzzer)
        buzzer_pwm.start(50)
        time.sleep(0.5)
        GPIO.output(pin_led, GPIO.LOW)
        buzzer_pwm.stop()
        time.sleep(intervalo)
    
    # Garantir que o LED seja desligado ao final
    GPIO.output(pin_led, GPIO.LOW)

# Função para registrar o acesso no arquivo CSV
def registrar_acesso(identificacao, nome, status):
    with open('acessos.csv', mode='a') as file:
        writer = csv.writer(file)
        horario = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        writer.writerow([identificacao, nome, status, horario])

# Função para verificar o acesso com base no RFID
def verificar_acesso(rfid_tag):
    if rfid_tag in funcionarios:
        funcionario = funcionarios[rfid_tag]
        if funcionario.autorizacao:
            print(f"Bem-vindo, {funcionario.nome}!")

            # Acender LED verde e tocar o buzzer simultaneamente
            GPIO.output(LED_VERDE_PIN, GPIO.HIGH)
            buzzer_pwm.ChangeFrequency(1000)
            buzzer_pwm.start(50)
            time.sleep(5)
            GPIO.output(LED_VERDE_PIN, GPIO.LOW)
            buzzer_pwm.stop()

            # Registrar a entrada do colaborador
            entrada_colaboradores[rfid_tag] = time.time()
            registrar_acesso(rfid_tag, funcionario.nome, 'Acesso Autorizado')
        else:
            print(f"Acesso negado para {funcionario.nome}!")
            tentativa_acesso_negado(rfid_tag, funcionario.nome)
    else:
        tentativa_invasao(rfid_tag)

# Função para lidar com tentativas de acesso negado
def tentativa_acesso_negado(rfid_tag, nome):
    global tentativas_nao_autorizadas
    print(f"Tentativa de acesso negado para {nome}!")
    piscar_led_com_buzzer(LED_VERMELHO_PIN, 400, 5, 0.5)

    # Registrar tentativas de acesso negado no dicionário
    if nome in tentativas_nao_autorizadas:
        tentativas_nao_autorizadas[nome] += 1
    else:
        tentativas_nao_autorizadas[nome] = 1

    # Registrar no arquivo CSV como 'Acesso Negado'
    registrar_acesso(rfid_tag, nome, 'Acesso Negado')

# Função para lidar com tentativas de invasão (RFID não reconhecido)
def tentativa_invasao(rfid_tag):
    global tentativas_invasao
    tentativas_invasao += 1
    print("Tentativa de invasão! Tag desconhecida.")
    piscar_led_com_buzzer(LED_VERMELHO_PIN, 300, 10, 0.5)
    registrar_acesso(rfid_tag, "Desconhecido", 'Tentativa de Invasão')

# Função para calcular o tempo de permanência
def calcular_tempo_permanencia(rfid_tag):
    if rfid_tag in entrada_colaboradores:
        entrada = entrada_colaboradores[rfid_tag]
        tempo_atual = time.time() - entrada
        return tempo_atual
    return 0

# Função para registrar a saída do colaborador
def registrar_saida(rfid_tag):
    if rfid_tag in entrada_colaboradores:
        tempo_permanencia[rfid_tag] = calcular_tempo_permanencia(rfid_tag)
        del entrada_colaboradores[rfid_tag]

# Função para mostrar o relatório final
def mostrar_relatorio():
    print("\n--- Relatório Final ---\n")
    print("Tempo de Permanência dos Colaboradores:")
    for rfid_tag, tempo in tempo_permanencia.items():
        funcionario = funcionarios.get(rfid_tag, Funcionario("Desconhecido", False))
        horas = tempo // 3600
        minutos = (tempo % 3600) // 60
        segundos = tempo % 60
        print(f"{funcionario.nome}: {int(horas)} horas, {int(minutos)} minutos e {int(segundos)} segundos")

    print("\nTentativas de Acesso Não Autorizado:")
    for nome, tentativas in tentativas_nao_autorizadas.items():
        print(f"{nome}: {tentativas} tentativas")

    print(f"\nTentativas de Invasão: {tentativas_invasao}")

# Loop principal para leitura de RFID e controle de acesso
try:
    while True:
        print("Aproxime o cartão RFID...")
        rfid_tag, text = reader.read()
        rfid_tag = str(rfid_tag)

        if rfid_tag:
            if rfid_tag in entrada_colaboradores:
                registrar_saida(rfid_tag)
            else:
                verificar_acesso(rfid_tag)
        time.sleep(1)

except KeyboardInterrupt:
    print("Programa encerrado pelo usuário.")
    mostrar_relatorio()
finally:
    GPIO.cleanup()
