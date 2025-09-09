import telebot
import os
import csv

# =========================
# CONFIGURAÇÕES
# =========================
BOT_TOKEN = os.getenv("8315294732:AAEJ9N31Gu0tC_PAmR34-jnNce14lHAyDEw")               # Token do @BotFather
CHAT_LOGS_ID = os.getenv("8245488250")        # Seu Telegram para receber logs
LINK_GRUPO_VIP = "https://t.me/+F0HUkrlAgjFiMzU8"  # Link do grupo VIP
VALOR = "10-15€"
IBAN = "LT94 3250 0541 9665 3953"
AUTOMATIC_APPROVE = True  # True = aprova automaticamente após envio de comprovante, False = aprovação manual

bot = telebot.TeleBot(BOT_TOKEN)
CSV_FILE = "pagamentos.csv"

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

# Inicializa CSV
inicializa_csv()

# =========================
# LOGS NO TELEGRAM
# =========================
def log_telegram(mensagem):
    try:
        bot.send_message(CHAT_LOGS_ID, mensagem)
    except Exception as e:
        print(f"Erro ao enviar log: {e}")

# =========================
# NOVO MEMBRO NO GRUPO (solicita entrada)
# =========================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(message):
    for member in message.new_chat_members:
        try:
            adicionar_usuario(member.id, member.first_name)
            bot.send_message(
                member.id,
                f"Olá {member.first_name}! 😏\n"
                f"Para entrar no grupo VIP, é necessário pagar {VALOR}.\n"
                f"IBAN: {IBAN}\n\n"
                "Após o pagamento, envie uma foto ou arquivo comprovando aqui.\n"
                "Se estiver configurado para aprovação automática, você será adicionado diretamente ao grupo!"
            )
            log_telegram(f"Novo usuário pendente: {member.first_name} ({member.id})")
        except:
            print(f"Não foi possível enviar mensagem privada para {member.first_name}")

# =========================
# RECEBIMENTO DE COMPROVANTE
# =========================
@bot.message_handler(content_types=["photo", "document"])
def receber_comprovante(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name
    if usuario_pendente(user_id):
        if AUTOMATIC_APPROVE:
            aprovar_usuario(user_id)
            bot.reply_to(message, f"Pagamento recebido! ✅ Você agora está aprovado para o grupo VIP.")
            bot.send_message(user_id, f"Aqui está o link do grupo VIP: {LINK_GRUPO_VIP}")
            log_telegram(f"Pagamento confirmado AUTOMATICAMENTE: {nome} ({user_id})")
        else:
            bot.reply_to(message, f"Recebemos seu comprovante, {nome}. ✅ Você será aprovado manualmente em breve.")
            log_telegram(f"Pagamento recebido (AGUARDANDO APROVAÇÃO): {nome} ({user_id})")
    else:
        bot.reply_to(message, "Você não possui pendência de pagamento ou já foi aprovado.")

# =========================
# COMANDO /aprovar MANUAL (somente se AUTOMATIC_APPROVE=False)
# =========================
@bot.message_handler(commands=["aprovar"])
def aprovar_manual(message):
    if AUTOMATIC_APPROVE:
        bot.reply_to(message, "Aprovação manual desativada, bot aprova automaticamente.")
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Use: /aprovar <user_id>")
        return
    user_id = args[1]
    aprovar_usuario(user_id)
    bot.send_message(user_id, f"Você foi aprovado no grupo VIP! Link: {LINK_GRUPO_VIP}")
    bot.reply_to(message, f"Usuário {user_id} aprovado com sucesso!")
    log_telegram(f"Usuário aprovado manualmente: {user_id}")

# =========================
# COMANDO /start
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Oi 👋 estou online 24h! Este é o bot do grupo VIP.")

# =========================
# RODA O BOT 24H
# =========================
bot.infinity_polling()
