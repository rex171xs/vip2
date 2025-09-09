import os
import telebot
import csv
from telebot import types

# =========================
# CONFIGURAÇÕES
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
LINK_GRUPO_VIP = "https://t.me/+F0HUkrlAgjFiMzU8"  # link VIP final
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
            writer.writerow(["user_id","nome","status"])  # pendente/pago

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
        f"🔥 Ei {nome}! VIP mais exclusivo esperando por você! 🔥\n\n"
        f"💰 Valor: {VALOR}\n"
        f"🏦 IBAN: {IBAN}\n\n"
        "Envie **somente foto ou PDF** como comprovante.\n"
        "💎 Apenas os rápidos e decididos entram!"
    )

# =========================
# NOVO MEMBRO NO GRUPO DE PRÉVIA
# =========================
@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(message):
    for member in message.new_chat_members:
        try:
            adicionar_usuario(member.id, member.first_name)
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("💎 Enviar comprovante", callback_data="enviar_comprovante")
            markup.add(btn)
            bot.send_message(
                member.id,
                f"Olá {member.first_name}! 👋\nVocê entrou no grupo de prévia.\n\n"
                "⚡ Clique no botão abaixo para iniciar seu acesso VIP!",
                reply_markup=markup
            )
        except Exception as e:
            print(f"Não foi possível enviar mensagem privada: {e}")

# =========================
# BOTÃO INLINE
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    nome = call.from_user.first_name

    if call.data == "enviar_comprovante":
        if usuario_pendente(user_id):
            bot.send_message(user_id, mensagem_agressiva(nome))
        else:
            bot.send_message(user_id, "Você já foi aprovado ou não possui pendência.")

# =========================
# RECEBENDO COMPROVANTE (VIP liberado automático)
# =========================
@bot.message_handler(content_types=["photo","document"])
def receber_comprovante(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name

    if usuario_pendente(user_id):
        # valida documento
        if message.content_type == "document":
            doc_name = message.document.file_name.lower()
            if not (doc_name.endswith(".jpg") or doc_name.endswith(".jpeg") or doc_name.endswith(".png") or doc_name.endswith(".pdf")):
                bot.send_message(user_id, "❌ Arquivo inválido! Apenas imagens ou PDF são aceitos.")
                return

        # aprova e envia VIP
        aprovar_usuario(user_id)
        bot.send_message(user_id, f"✅ Pagamento confirmado! Aqui está seu link VIP: {LINK_GRUPO_VIP}")
    else:
        bot.reply_to(message, "Você não possui pendência ou já foi aprovado.")

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
# RODA 24H
# =========================
bot.infinity_polling(timeout=10,long_polling_timeout=5)
