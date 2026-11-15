import os
import sqlite3
from datetime import date, timedelta

# No servidor, DB_PATH aponta para a pasta que não é apagada (/data). No PC, usa artemis.db.
ARQUIVO = os.getenv("DB_PATH", "artemis.db")


def conectar():
    return sqlite3.connect(ARQUIVO)


def criar_tabelas():
    with conectar() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                prazo TEXT,
                concluida INTEGER DEFAULT 0
            )
        """)
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                valor REAL NOT NULL,
                categoria TEXT,
                descricao TEXT,
                data TEXT DEFAULT CURRENT_DATE
            )
        """)


def adicionar_tarefa(descricao, prazo=None):
    with conectar() as conexao:
        conexao.execute(
            "INSERT INTO tarefas (descricao, prazo) VALUES (?, ?)",
            (descricao, prazo),
        )


def listar_tarefas():
    with conectar() as conexao:
        return conexao.execute(
            "SELECT id, descricao, prazo FROM tarefas WHERE concluida = 0 ORDER BY prazo"
        ).fetchall()


def tarefas_proximas(dias):
    limite = (date.today() + timedelta(days=dias)).isoformat()
    with conectar() as conexao:
        return conexao.execute(
            "SELECT id, descricao, prazo FROM tarefas "
            "WHERE concluida = 0 AND prazo IS NOT NULL AND prazo <= ? "
            "ORDER BY prazo",
            (limite,),
        ).fetchall()


def concluir_tarefa(id_tarefa):
    with conectar() as conexao:
        cursor = conexao.execute(
            "UPDATE tarefas SET concluida = 1 WHERE id = ? AND concluida = 0",
            (id_tarefa,),
        )
        return cursor.rowcount > 0


def adicionar_gasto(valor, categoria, descricao=""):
    hoje = date.today().isoformat()
    with conectar() as conexao:
        conexao.execute(
            "INSERT INTO gastos (valor, categoria, descricao, data) VALUES (?, ?, ?, ?)",
            (valor, categoria, descricao, hoje),
        )


def listar_gastos():
    with conectar() as conexao:
        return conexao.execute(
            "SELECT id, valor, categoria, descricao, data FROM gastos ORDER BY data DESC"
        ).fetchall()


def gastos_por_categoria(inicio, fim):
    with conectar() as conexao:
        return conexao.execute(
            "SELECT categoria, SUM(valor) FROM gastos "
            "WHERE data BETWEEN ? AND ? "
            "GROUP BY categoria ORDER BY SUM(valor) DESC",
            (inicio, fim),
        ).fetchall()