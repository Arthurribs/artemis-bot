# 🏹 Artemis — Assistente pessoal com IA no Telegram

Assistente pessoal que organiza **tarefas** e **finanças** pelo Telegram. Em vez de decorar comandos, basta escrever naturalmente — *"gastei 35 no uber"*, *"anota pra eu estudar cálculo até sexta"*, *"quanto gastei com comida esse mês?"* — e um **agente de IA** decide sozinho o que fazer.

Inclui lembretes automáticos de prazos e um painel web com gráficos de gastos e tarefas.

> 📸 *Adicione aqui um print ou GIF do bot e do dashboard funcionando.*

---

## ✨ Funcionalidades

- 🧠 **Agente de IA (Gemini + function calling):** entende linguagem natural e escolhe a ferramenta certa (registrar gasto, criar tarefa, concluir tarefa, resumir gastos por período)
- 📝 **Lista de tarefas** com prazos (`/tarefa`, `/lista`, `/feito`)
- 💸 **Controle de gastos** por categoria (`/gasto`, `/gastos`)
- ⏰ **Lembretes automáticos:** todo dia às 8h, avisa o que vence nos próximos 3 dias (e o que está atrasado)
- 📊 **Dashboard** em Streamlit com métricas, gráficos e filtro de período
- 🔒 **Acesso restrito:** o bot só responde ao dono (filtro por `chat_id`)

## 🧠 Como o agente funciona

1. O usuário envia uma mensagem livre no Telegram.
2. O bot envia a mensagem ao Gemini junto com a lista de **ferramentas** disponíveis — funções Python com tipos e docstrings descrevendo o que fazem.
3. O modelo decide qual ferramenta chamar e com quais argumentos (ex.: `registrar_gasto(valor=35, categoria="transporte", descricao="uber")`).
4. A função é executada no banco de dados e o resultado volta para o modelo, que escreve a resposta final.

As instruções de sistema incluem a data atual, para o agente interpretar expressões como *"sexta"* ou *"esse mês"*, e uma lista fixa de categorias, para manter os dados consistentes.

## 🛠️ Tecnologias

| Parte | Tecnologia |
|---|---|
| Linguagem | Python 3.13 |
| Bot | python-telegram-bot (com JobQueue para os lembretes) |
| IA | Google Gemini API (`google-genai`), function calling |
| Banco de dados | SQLite |
| Dashboard | Streamlit + pandas |

## 📁 Estrutura

```
├── bot.py          # Bot do Telegram: comandos, lembretes e integração com o agente
├── agente.py       # Agente de IA: ferramentas, instruções e chamada ao Gemini
├── database.py     # Acesso ao banco SQLite (tarefas e gastos)
├── dashboard.py    # Painel web em Streamlit
├── requirements.txt
└── .env.example    # Modelo das variáveis de ambiente
```

## 🚀 Como rodar

**1. Clone e instale as dependências**
```bash
git clone https://github.com/SEU_USUARIO/artemis-bot.git
cd artemis-bot
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

**2. Configure as variáveis de ambiente**

Copie o `.env.example` para `.env` e preencha:
- `TELEGRAM_TOKEN`: token do bot, obtido com o [@BotFather](https://t.me/BotFather)
- `GEMINI_API_KEY`: chave gratuita no [Google AI Studio](https://aistudio.google.com)
- `CHAT_ID`: seu ID no Telegram (rode o bot e envie `/meuid`)

**3. Rode o bot**
```bash
python bot.py
```

**4. Rode o dashboard** (em outro terminal)
```bash
streamlit run dashboard.py
```

## 💬 Exemplos de uso

| Você escreve | O Artemis faz |
|---|---|
| `35 uber` | Registra R$ 35,00 em transporte |
| `anota pra eu pagar a fatura dia 18` | Cria a tarefa com prazo em 18/11 |
| `terminei a de pagar a fatura` | Encontra a tarefa e marca como concluída |
| `quanto gastei com comida esse mês?` | Soma os gastos de alimentação do mês |

## 🗺️ Próximos passos

- [ ] Deploy em nuvem para funcionar 24h
- [ ] Memória de conversa (histórico de mensagens no agente)
- [ ] Migrar de SQLite para PostgreSQL em produção
- [ ] Orçamento mensal por categoria com alertas
- [ ] Testes automatizados

## 👤 Autor

**Arthur Ribeiro dos Santos** — estudante de Análise e Desenvolvimento de Sistemas (Universidade Veiga de Almeida)

[LinkedIn](https://linkedin.com/in/SEU_PERFIL) · [E-mail](mailto:arthurrib07@gmail.com)
