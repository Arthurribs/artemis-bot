import asyncio
import os
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from database import (
    criar_tabelas,
    adicionar_tarefa,
    listar_tarefas,
    tarefas_proximas,
    concluir_tarefa,
    adicionar_gasto,
    listar_gastos,
)

from agente import responder

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

FUSO = ZoneInfo("America/Sao_Paulo")
HORARIO_LEMBRETE = time(hour=8, minute=0, tzinfo=FUSO)
DIAS_DE_AVISO = 3


# ---------- Funções de apoio ----------

def converter_data(texto):
    """Transforma '18/11' em '2026-11-18'. Se não for uma data, devolve None."""
    hoje = datetime.now()
    try:
        data = datetime.strptime(f"{texto}/{hoje.year}", "%d/%m/%Y")
    except ValueError:
        return None
    if data.date() < hoje.date():
        data = data.replace(year=hoje.year + 1)
    return data.strftime("%Y-%m-%d")


def formatar_data(data_banco):
    """Transforma '2026-11-18' em '18/11'."""
    return datetime.strptime(data_banco, "%Y-%m-%d").strftime("%d/%m")


def formatar_reais(valor):
    """Transforma 35.9 em 'R$ 35,90'."""
    return f"R$ {valor:.2f}".replace(".", ",")


def quanto_falta(prazo):
    """Diz em português quanto tempo falta para o prazo."""
    dias = (date.fromisoformat(prazo) - date.today()).days
    if dias < 0:
        return f"⚠️ atrasada há {-dias} dia(s)"
    if dias == 0:
        return "🔥 é HOJE"
    if dias == 1:
        return "é amanhã"
    return f"faltam {dias} dias"


# ---------- Lembretes ----------

async def enviar_lembrete(context: ContextTypes.DEFAULT_TYPE):
    """Manda a lista de tarefas próximas. Devolve True se mandou algo."""
    tarefas = tarefas_proximas(DIAS_DE_AVISO)
    if not tarefas:
        return False

    linhas = ["⏰ Bom dia! Olha o que vem por aí:\n"]
    for id_tarefa, descricao, prazo in tarefas:
        linhas.append(f"{id_tarefa}. {descricao} ({formatar_data(prazo)}) → {quanto_falta(prazo)}")

    await context.bot.send_message(chat_id=CHAT_ID, text="\n".join(linhas))
    return True


async def lembrete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /lembrete: dispara o lembrete na hora, para testar."""
    mandou = await enviar_lembrete(context)
    if not mandou:
        await update.message.reply_text(f"Nada vencendo nos próximos {DIAS_DE_AVISO} dias. 😎")


# ---------- Comandos ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.effective_user.first_name
    await update.message.reply_text(
        f"Fala, {nome}! Eu sou o Artemis. Veja o que eu sei fazer:\n\n"
        "📝 /tarefa Pagar fatura 18/11 → anota uma tarefa\n"
        "📋 /lista → mostra suas tarefas\n"
        "✅ /feito 2 → conclui a tarefa número 2\n"
        "💸 /gasto 35,90 alimentação almoço → registra um gasto\n"
        "📊 /gastos → mostra seus gastos\n"
        "⏰ /lembrete → mostra agora o que vence em breve"
    )


async def meuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Seu chat_id é: {update.effective_chat.id}")


async def tarefa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Me diz a tarefa. Ex.: /tarefa Pagar fatura 18/11")
        return

    prazo = converter_data(context.args[-1])
    if prazo:
        descricao = " ".join(context.args[:-1])
    else:
        descricao = " ".join(context.args)

    if not descricao:
        await update.message.reply_text("Faltou a descrição. Ex.: /tarefa Pagar fatura 18/11")
        return

    adicionar_tarefa(descricao, prazo)

    if prazo:
        await update.message.reply_text(f"📝 Anotado: {descricao} (até {formatar_data(prazo)})")
    else:
        await update.message.reply_text(f"📝 Anotado: {descricao} (sem prazo)")


async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tarefas = listar_tarefas()
    if not tarefas:
        await update.message.reply_text("Nenhuma tarefa pendente. 🎉")
        return

    linhas = ["📋 Suas tarefas:\n"]
    for id_tarefa, descricao, prazo in tarefas:
        if prazo:
            linhas.append(f"{id_tarefa}. {descricao} → até {formatar_data(prazo)}")
        else:
            linhas.append(f"{id_tarefa}. {descricao}")

    await update.message.reply_text("\n".join(linhas))


async def feito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Me diz o número da tarefa. Ex.: /feito 2 (veja os números em /lista)")
        return

    if concluir_tarefa(int(context.args[0])):
        await update.message.reply_text("✅ Tarefa concluída! Mandou bem.")
    else:
        await update.message.reply_text("Não achei essa tarefa pendente. Confira o número em /lista.")


async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Me diz o gasto. Ex.: /gasto 35,90 alimentação almoço")
        return

    try:
        valor = float(context.args[0].replace(",", "."))
    except ValueError:
        await update.message.reply_text("O primeiro item precisa ser o valor. Ex.: /gasto 35,90 alimentação almoço")
        return

    categoria = context.args[1] if len(context.args) > 1 else "outros"
    descricao = " ".join(context.args[2:])

    adicionar_gasto(valor, categoria, descricao)
    await update.message.reply_text(f"💸 Registrado: {formatar_reais(valor)} em {categoria}")


async def gastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registros = listar_gastos()
    if not registros:
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return

    total = sum(registro[1] for registro in registros)

    linhas = ["📊 Seus últimos gastos:\n"]
    for _, valor, categoria, descricao, data in registros[:10]:
        linhas.append(f"{formatar_data(data)} • {formatar_reais(valor)} • {categoria} {descricao}")
    linhas.append(f"\nTotal geral: {formatar_reais(total)}")

    await update.message.reply_text("\n".join(linhas))


async def conversar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        texto = await asyncio.to_thread(responder, update.message.text)
    except Exception as erro:
        print(f"Erro na IA: {erro}")
        texto = "Tive um problema para falar com a IA. 😕 Tente de novo em instantes ou use os comandos (/start)."
    await update.message.reply_text(texto)


# ---------- Ligar o bot ----------

def main():
    criar_tabelas()

    if CHAT_ID:
        so_eu = filters.Chat(chat_id=int(CHAT_ID))
    else:
        print("⚠️ CHAT_ID não configurado: o bot está aberto para qualquer pessoa. Use /meuid.")
        so_eu = filters.ALL

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("meuid", meuid))
    app.add_handler(CommandHandler("start", start, filters=so_eu))
    app.add_handler(CommandHandler("tarefa", tarefa, filters=so_eu))
    app.add_handler(CommandHandler("lista", lista, filters=so_eu))
    app.add_handler(CommandHandler("feito", feito, filters=so_eu))
    app.add_handler(CommandHandler("gasto", gasto, filters=so_eu))
    app.add_handler(CommandHandler("gastos", gastos, filters=so_eu))
    app.add_handler(CommandHandler("lembrete", lembrete, filters=so_eu))
    app.add_handler(MessageHandler(so_eu & filters.TEXT & ~filters.COMMAND, conversar))

    if CHAT_ID:
        app.job_queue.run_daily(enviar_lembrete, time=HORARIO_LEMBRETE)
        print(f"Lembrete diário agendado para {HORARIO_LEMBRETE.strftime('%H:%M')}.")

    print("Artemis rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()