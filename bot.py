import os
import telebot
import csv
from telebot import types

# =========================
# VARIÁVEIS
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
LINK_GRUPO_VIP = "https://t.me/+KJmxLUcAUIllNTU0"  # link do grupo VIP
VALOR = "10-15€"
IBAN = "LT94 3250 0541 9665 3953"
CSV_FILE = "pagamentos.csv"

# =========================
# CSV
# =========================
def inicializa_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id","nome","status"])  # status = pendente/pago

def adicionar_usuario(user_id, nome):
    if not usuario_existe(user_id):
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([user_id,nome,"pendente"])

def aprovar_usuario(user_id):
    rows=[]
    with open(CSV_FILE,"r",encoding="utf-8") as f:
        reader=csv.reader(f)
        for row in reader:
            if row[0]==str(user_id):
                row[2]="pago"
            rows.append(row)
    with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def usuario_pendente(user_id):
    with open(CSV_FILE,"r",encoding="utf-8") as f:
        reader=csv.reader(f)
        for row in reader:
            if row[0]==str(user_id) and row[2]=="pendente":
                return True
    return False

def usuario_existe(user_id):
    with open(CSV_FILE,"r",encoding="utf-8") as f:
        reader=csv.reader(f)
        for row in reader:
            if row[0]==str(user_id):
                return True
    return False

inicializa_csv()

# =========================
# INICIALIZA BOT
# =========================
bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# MENSAGEM AGRESSIVA
# =========================
def mensagem_agressiva(nome):
    return (
        f"🔥 Ei {nome}! Você pode entrar no VIP mais exclusivo! 🔥\n\n"
        f">> O valor para entrar é {VALOR}.\n"
        f">> IBAN para pagamento: {IBAN}\n\n"
        ">> Envie uma foto ou documento como comprovativo.\n"
        "💎 Apenas os rápidos e decididos entram!"
    )

# =========================
# /start
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name

    adicionar_usuario(user_id, nome)

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("💎 Enviar comprovante", callback_data="enviar_comprovante")
    markup.add(btn)

    bot.send_message(user_id, mensagem_agressiva(nome), reply_markup=markup)

# =========================
# BOTÃO INLINE
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    nome = call.from_user.first_name

    if call.data == "enviar_comprovante":
        if usuario_pendente(user_id):
            bot.send_message(user_id, f"{nome}, envie aqui seu comprovante (foto ou documento).")
        else:
            bot.send_message(user_id, "Você já foi aprovado ou não possui pendência.")

# =========================
# RECEBENDO COMPROVANTE (aprovacao manual)
# =========================
@bot.message_handler(content_types=["photo","document"])
def receber_comprovante(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name

    if usuario_pendente(user_id):
        bot.send_message(user_id, "✅ Comprovante recebido! Sua entrada será liberada após aprovação manual.")
    else:
        bot.reply_to(message, "Você não possui pendência ou já foi aprovado.")

# =========================
# COMANDO PARA APROVAR MANUALMENTE
# =========================
@bot.message_handler(commands=["aprovar"])
def comando_aprovar(message):
    args = message.text.split()
    if len(args) == 2 and args[1].isdigit():
        user_id = int(args[1])
        if usuario_pendente(user_id):
            aprovar_usuario(user_id)
            bot.send_message(user_id, f"🎉 Parabéns! Você agora tem acesso ao VIP: {LINK_GRUPO_VIP}")
            bot.reply_to(message, f"Usuário {user_id} aprovado com sucesso.")
        else:
            bot.reply_to(message, "Usuário não encontrado ou já aprovado.")
    else:
        bot.reply_to(message, "Uso correto: /aprovar <user_id>")

# =========================
# RODA BOT 24H
# =========================
bot.infinity_polling(timeout=10,long_polling_timeout=5)
