import os
import telebot
import csv
import time
from telebot import types

# =========================
# VARIÁVEIS DE AMBIENTE
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_LOGS_ID = os.getenv("CHAT_LOGS_ID")
LINK_GRUPO_VIP = "https://t.me/+F0HUkrlAgjFiMzU8"  # link do grupo VIP
VALOR = "10-15€"
IBAN = "LT94 3250 0541 9665 3953"
AUTOMATIC_APPROVE = True  # True = aprova automaticamente, False = manual
CSV_FILE = "pagamentos.csv"

# =========================
# CHECAGEM DE VARIÁVEIS
# =========================
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN não está definido! Verifique as variáveis de ambiente.")
if not CHAT_LOGS_ID:
    raise ValueError("CHAT_LOGS_ID não está definido! Verifique as variáveis de ambiente.")

# =========================
# FUNÇÕES AUXILIARES CSV
# =========================
def inicializa_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "nome", "status"])  # status = pendente/pago

def adicionar_usuario(user_id, nome):
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, nome, "pendente"])

def aprovar_usuario(user_id):
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == str(user_id):
                row[2] = "pago"
            rows.append(row)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def usuario_pendente(user_id):
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == str(user_id) and row[2] == "pendente":
                return True
    return False

# =========================
# INICIALIZA CSV
# =========================
inicializa_csv()

# =========================
# INICIALIZA BOT
# =========================
bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# FUNÇÃO DE LOG NO TELEGRAM
# =========================
def log_telegram(mensagem):
    try:
        bot.send_message(CHAT_LOGS_ID, mensagem)
    except Exception as e:
        print("Erro enviando log:", e)

# =========================
# PROTEÇÃO ANTI-FLOOD
# =========================
usuarios_ativos = {}  # user_id: timestamp
TEMPO_ESPERA = 60  # segundos entre /start

def pode_iniciar(user_id):
    agora = time.time()
    if user_id in usuarios_ativos:
        if agora - usuarios_ativos[user_id] < TEMPO_ESPERA:
            return False
    usuarios_ativos[user_id] = agora
    return True

# =========================
# EVENTO NOVO MEMBRO NO GRUPO DE PRÉVIA
# =========================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(message):
    for member in message.new_chat_members:
        try:
            adicionar_usuario(member.id, member.first_name)
            bot.send_message(
                member.id,
                f"Olá {member.first_name}! 👋\n"
                f"Você entrou no grupo de prévia.\n"
                f"Para acessar o grupo VIP, é necessário pagar {VALOR}.\n"
                f"IBAN: {IBAN}\n\n"
                "Após o pagamento, envie uma foto ou arquivo comprovando aqui.\n"
                "Se estiver configurado para aprovação automática, você será adicionado diretamente ao VIP!"
            )
            log_telegram(f"Novo usuário pendente: {member.first_name} ({member.id})")
        except Exception as e:
            print(f"Não foi possível enviar mensagem privada para {member.first_name}: {e}")

# =========================
# RECEBER COMPROVANTE
# =========================
@bot.message_handler(content_types=["photo", "document"])
def receber_comprovante(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name
    if usuario_pendente(user_id):
        if AUTOMATIC_APPROVE:
            aprovar_usuario(user_id)
            bot.send_message(user_id, f"Pagamento recebido! ✅ Aqui está o link do grupo VIP: {LINK_GRUPO_VIP}")
            log_telegram(f"Pagamento confirmado AUTOMATICAMENTE: {nome} ({user_id})")
        else:
            bot.send_message(user_id, f"Recebemos seu comprovante, {nome}. ✅ Você será aprovado manualmente em breve.")
            log_telegram(f"Pagamento recebido (AGUARDANDO APROVAÇÃO): {nome} ({user_id})")
    else:
        bot.reply_to(message, "Você não possui pendência de pagamento ou já foi aprovado.")

# =========================
# COMANDO /start
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name

    if not pode_iniciar(user_id):
        bot.reply_to(message, f"Espere {TEMPO_ESPERA} segundos antes de usar /start novamente.")
        return

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("💎 Entrar no VIP", url=LINK_GRUPO_VIP)
    markup.add(btn)

    bot.send_message(
        user_id,
        f"Oi {nome}! 👋\n"
        "Bem-vindo ao bot VIP!\n\n"
        f"Para liberar sua entrada no VIP, clique no botão abaixo e siga as instruções de pagamento ({VALOR}):",
        reply_markup=markup
    )

    log_telegram(f"Usuário iniciou /start: {nome} ({user_id})")

# =========================
# RODA O BOT 24H
# =========================
try:
    log_telegram("Bot iniciado com sucesso ✅")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except Exception as e:
    print("Erro no polling:", e)
    log_telegram(f"Erro no polling: {e}")
