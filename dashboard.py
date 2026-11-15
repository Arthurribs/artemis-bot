from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database import conectar, criar_tabelas

st.set_page_config(page_title="Artemis", page_icon="🏹", layout="wide")
criar_tabelas()


# ---------- Carregar dados ----------

def carregar_tarefas():
    with conectar() as conexao:
        return pd.read_sql_query(
            "SELECT id, descricao, prazo FROM tarefas WHERE concluida = 0 ORDER BY prazo",
            conexao,
        )


def carregar_gastos():
    with conectar() as conexao:
        return pd.read_sql_query(
            "SELECT valor, categoria, descricao, data FROM gastos",
            conexao,
        )


def reais(valor):
    """Transforma 1234.5 em 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------- Filtro de período ----------

hoje = date.today()

st.sidebar.header("Filtros")
periodo = st.sidebar.radio("Período dos gastos", ["Este mês", "Últimos 30 dias", "Tudo"])

if periodo == "Este mês":
    inicio = hoje.replace(day=1)
elif periodo == "Últimos 30 dias":
    inicio = hoje - timedelta(days=30)
else:
    inicio = date(2000, 1, 1)

tarefas = carregar_tarefas()
gastos = carregar_gastos()

gastos["data"] = pd.to_datetime(gastos["data"])
gastos_periodo = gastos[gastos["data"] >= pd.Timestamp(inicio)]

prazos = pd.to_datetime(tarefas["prazo"])
hoje_ts = pd.Timestamp(hoje)
atrasadas = int((prazos < hoje_ts).sum())
vencendo = int(((prazos >= hoje_ts) & (prazos <= hoje_ts + pd.Timedelta(days=3))).sum())


# ---------- Topo ----------

st.title("🏹 Artemis: painel pessoal")
st.caption(f"Hoje é {hoje.strftime('%d/%m/%Y')}. Atualize a página (F5) para ver dados novos.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💸 Gasto no período", reais(gastos_periodo["valor"].sum()))
col2.metric("📋 Tarefas pendentes", len(tarefas))
col3.metric("⏰ Vencem em 3 dias", vencendo)
col4.metric("⚠️ Atrasadas", atrasadas)

st.divider()


# ---------- Gráficos ----------

esquerda, direita = st.columns(2)

with esquerda:
    st.subheader("Gastos por categoria")
    if gastos_periodo.empty:
        st.info("Nenhum gasto nesse período.")
    else:
        por_categoria = (
            gastos_periodo.groupby("categoria")["valor"].sum().sort_values(ascending=False)
        )
        st.bar_chart(por_categoria)

with direita:
    st.subheader("Gastos por dia")
    if gastos_periodo.empty:
        st.info("Nenhum gasto nesse período.")
    else:
        por_dia = gastos_periodo.groupby(gastos_periodo["data"].dt.date)["valor"].sum()
        st.bar_chart(por_dia)


# ---------- Tabelas ----------

def situacao(prazo):
    if pd.isna(prazo):
        return "sem prazo"
    dias = (prazo.date() - hoje).days
    if dias < 0:
        return f"⚠️ atrasada há {-dias} dia(s)"
    if dias == 0:
        return "🔥 hoje"
    if dias == 1:
        return "amanhã"
    return f"em {dias} dias"


st.subheader("Tarefas pendentes")
if tarefas.empty:
    st.success("Nenhuma tarefa pendente! 🎉")
else:
    tabela_tarefas = pd.DataFrame({
        "Nº": tarefas["id"],
        "Tarefa": tarefas["descricao"],
        "Prazo": prazos.dt.strftime("%d/%m").fillna("—"),
        "Situação": prazos.apply(situacao),
    })
    st.dataframe(tabela_tarefas, hide_index=True)

st.subheader("Últimos gastos")
if gastos_periodo.empty:
    st.info("Nenhum gasto nesse período.")
else:
    ultimos = gastos_periodo.sort_values("data", ascending=False).head(15)
    tabela_gastos = pd.DataFrame({
        "Data": ultimos["data"].dt.strftime("%d/%m"),
        "Valor": ultimos["valor"].apply(reais),
        "Categoria": ultimos["categoria"],
        "Descrição": ultimos["descricao"],
    })
    st.dataframe(tabela_gastos, hide_index=True)