# Nano Bank

A small FastAPI + SQLite banking API for classroom exercises. The `chatbot`, `rag`, and `agent` functions are placeholders for students to implement.

## Run

Requires Python 3.10+ and `uv`. From this folder:

```bash
# Skip if `pyproject.toml` already exists.
# It means python environment is initialized
uv init # LIKE git init 
uv add fastapi uvicorn sqlmodel faker loguru httpx # LIKE git add <file_name>
uv sync
```

```bash
# Running the program, always use UV to run
uv run nano-bank.py
```

Open http://127.0.0.1:8000/docs to try the API.

## Run the client

Keep the server running. In a second terminal, from this folder:

```bash
uv run nano-bank-client.py
```

The client prints a statement, deposits 500 USD, withdraws 100 USD, and prints the updated statement. Each run adds these transactions to the database.

## Try it

The seeded account is **ACC101**, owned by Alice, with a balance of **157,840 USD** after 12 monthly deposits and withdrawals from 2025. All amounts are positive whole dollars.

- `POST /accounts/ACC101/deposit` — JSON body: `{"amount": 500}`
- `POST /accounts/ACC101/withdraw` — JSON body: `{"amount": 100}`
- `GET /accounts/ACC101/statement/2025/1` — January transactions and totals, plus the account's current balance.

New transactions use the fixed classroom date **2026-11-06**. View them with `/accounts/ACC101/statement/2026/11`.

Invalid amounts return `422`, unknown accounts return `404`, and insufficient funds return `409`.

Data persists in `nano_bank_simple.db` in the working directory. To reset, stop the server and delete that file before restarting. Set `BANK_DATABASE_URL` to use a different SQLite file.

This snippet uses a shared database session for sequential, single-user classroom requests.
