from datetime import date
from dotenv import load_dotenv
from google import genai
from google.genai import types

from database import (
    adicionar_tarefa,
    listar_tarefas,
    concluir_tarefa,
    adicionar_gasto,
    gastos_por_categoria,
)

load_dotenv()

MODELO = "gemini-3.5-flash"
client = genai.Client()

CATEGORIAS = "alimentação, transporte, moradia, contas, lazer, saúde, educação, compras, outros"
DIAS_DA_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


# ---------- Ferramentas que a IA pode usar ----------

def registrar_gasto(valor: float, categoria: str, descricao: str = "") -> str:
    """Registra um gasto do usuário.

    Args:
        valor: Valor gasto em reais, por exemplo 35.90.
        categoria: Uma destas categorias: alimentação, transporte, moradia, contas, lazer, saúde, educação, compras, outros.
        descricao: Descrição curta do gasto, por exemplo "almoço" ou "uber pra faculdade".
    """
    adicionar_gasto(valor, categoria, descricao)
    return f"Gasto de {valor:.2f} reais registrado em {categoria}."


def criar_tarefa(descricao: str, prazo: str = "") -> str:
    """Cria uma tarefa na lista de afazeres do usuário.

    Args:
        descricao: O que precisa ser feito, por exemplo "Pagar fatura do cartão".
        prazo: Data limite no formato AAAA-MM-DD. Deixe vazio se o usuário não disse prazo.
    """
    adicionar_tarefa(descricao, prazo or None)
    return f"Tarefa '{descricao}' criada."


def ver_tarefas() -> list:
    """Lista as tarefas pendentes do usuário, com número (id), descrição e prazo (AAAA-MM-DD ou vazio)."""
    return [
        {"id": id_tarefa, "descricao": descricao, "prazo": prazo or ""}
        for id_tarefa, descricao, prazo in listar_tarefas()
    ]


def marcar_como_feita(id_tarefa: int) -> str:
    """Marca uma tarefa como concluída. Use ver_tarefas antes para descobrir o número (id) da tarefa.

    Args:
        id_tarefa: O número (id) da tarefa.
    """
    if concluir_tarefa(id_tarefa):
        return f"Tarefa {id_tarefa} concluída."
    return f"Não existe tarefa pendente com o número {id_tarefa}."


def resumo_gastos(data_inicio: str, data_fim: str) -> dict:
    """Soma os gastos do usuário em um período, por categoria.

    Args:
        data_inicio: Primeiro dia do período, no formato AAAA-MM-DD.
        data_fim: Último dia do período, no formato AAAA-MM-DD.
    """
    linhas = gastos_por_categoria(data_inicio, data_fim)
    por_categoria = {categoria: round(total, 2) for categoria, total in linhas}
    return {"total": round(sum(por_categoria.values()), 2), "por_categoria": por_categoria}


FERRAMENTAS = [registrar_gasto, criar_tarefa, ver_tarefas, marcar_como_feita, resumo_gastos]


# ---------- Instruções e resposta ----------

def instrucoes():
    hoje = date.today()
    return f"""Você é o Artemis, assistente pessoal do Arthur no Telegram.
Hoje é {DIAS_DA_SEMANA[hoje.weekday()]}, {hoje.isoformat()}.

Você ajuda a organizar tarefas e finanças usando as ferramentas disponíveis.

Regras:
- Ao chamar ferramentas, use datas no formato AAAA-MM-DD. Converta "amanhã", "sexta", "dia 20" e "esse mês" a partir da data de hoje.
- Use somente estas categorias de gasto: {CATEGORIAS}. Ex.: "comida" é alimentação, "uber" é transporte.
- Para concluir uma tarefa pelo nome, use ver_tarefas primeiro para achar o número dela.
- Nunca invente dados. Para perguntas sobre tarefas ou gastos, consulte as ferramentas.
- Se faltar informação (por exemplo, o valor de um gasto), pergunte em vez de adivinhar.
- Responda em português, de forma curta e amigável, com no máximo um emoji.
- Para o usuário, mostre valores como R$ 35,90 e datas como DD/MM.
"""


def responder(mensagem: str) -> str:
    resposta = client.models.generate_content(
        model=MODELO,
        contents=mensagem,
        config=types.GenerateContentConfig(
            system_instruction=instrucoes(),
            tools=FERRAMENTAS,
        ),
    )
    return resposta.text or "Hmm, não consegui entender. Pode reformular?"