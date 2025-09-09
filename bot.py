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
LINK_GRUPO_VIP = "https://t.me/+F0HUkrlAgjFiMzU8"  # link do grupo VIP final
VALOR = "10-15€"
IBAN = "LT94 3250 0541 9665 3953"
AUTOMATIC_APPROVE = True
CSV_FILE = "pagamentos.csv"

# =========================
# CHECAGEM DE VARIÁVEIS
# =========================
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN não definido")
if not CHAT_LOGS_ID:
    raise ValueError("CHAT_LOGS_ID não definido")

# =========================
# CSV
# =========================
def inicializa_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id","nome","status"])

def adicionar_usuario(user_id, nome):
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
        writer=csv.writer(f)
        writer.writerows(rows)

def usuario_pendente(user_id):
    with open(CSV_FILE,"r",encoding="utf-8") as f:
        reader=csv.reader(f)
        for row in reader:
            if row[0]==str(user_id) and row[2]=="pendente":
                return True
    return False

inicializa_csv()

# =========================
# INICIALIZA BOT
# =========================
bot = telebot.TeleBot(BOT_TOKEN)
usuarios_ativos = {}
TEMPO_ESPERA = 30  # anti-flood

def log_telegram(msg):
    try:
        bot.send_message(CHAT_LOGS_ID,msg)
    except Exception as e:
        print("Erro enviando log:", e)

def pode_iniciar(user_id):
    agora=time.time()
    if user_id in usuarios_ativos and agora-usuarios_ativos[user_id]<TEMPO_ESPERA:
        return False
    usuarios_ativos[user_id]=agora
    return True

# =========================
# FUNÇÃO PARA MENSAGEM AGRESSIVA
# =========================
def mensagem_agressiva(nome):
    return (
        f"🔥 Ei {nome}! Você acabou de ganhar a chance de entrar no VIP mais exclusivo! 🔥\n\n"
        "Não perca tempo, vagas limitadíssimas!\n"
        f"O valor para entrar é {VALOR}.\n"
        f"IBAN para pagamento: {IBAN}\n\n"
        "Assim que enviar o comprovante, você garante acesso imediato ao grupo VIP.\n"
        "💎 Somente os rápidos e decididos entram!"
    )

# =========================
# INICIO AUTOMÁTICO SEM /start
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name

    if not pode_iniciar(user_id):
        bot.reply_to(message, f"Espere {TEMPO_ESPERA} segundos antes de tentar novamente.")
        return

    if not usuario_pendente(user_id):
        adicionar_usuario(user_id, nome)

    # botão para enviar comprovante
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("💎 Enviar comprovante", callback_data="enviar_comprovante")
    markup.add(btn)

    bot.send_message(user_id, mensagem_agressiva(nome), reply_markup=markup)
    log_telegram(f"{nome} iniciou conversa VIP ({user_id})")

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
            log_telegram(f"{nome} clicou para enviar comprovante ({user_id})")
        else:
            bot.send_message(user_id, "Você já foi aprovado ou não possui pendência.")

# =========================
# RECEBENDO COMPROVANTE
# =========================
@bot.message_handler(content_types=["photo","document"])
def receber_comprovante(message):
    user_id = message.from_user.id
    nome = message.from_user.first_name

    if usuario_pendente(user_id):
        if AUTOMATIC_APPROVE:
            aprovar_usuario(user_id)
            bot.send_message(user_id,f"✅ Pagamento confirmado! Aqui está seu link VIP: {LINK_GRUPO_VIP}")
            log_telegram(f"{nome} aprovado automaticamente ({user_id})")
        else:
            bot.send_message(user_id,"Recebemos seu comprovante! ✅ Você será aprovado manualmente em breve.")
            log_telegram(f"{nome} enviou comprovante (aguardando aprovação) ({user_id})")
    else:
        bot.reply_to(message,"Você não possui pendência ou já foi aprovado.")

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
                "Você entrou no grupo de prévia.\n\n"
                "⚡ Clique no botão do bot para iniciar o processo VIP e garantir sua entrada exclusiva!"
            )
            log_telegram(f"Novo membro aprovado na prévia: {member.first_name} ({member.id})")
        except Exception as e:
            print(f"Não foi possível enviar mensagem privada: {e}")

# =========================
# RODA O BOT 24H
# =========================
try:
    log_telegram("Bot VIP iniciado com sucesso ✅")
    bot.infinity_polling(timeout=10,long_polling_timeout=5)
except Exception as e:
    print("Erro no polling:",e)
    log_telegram(f"Erro no polling: {e}")
