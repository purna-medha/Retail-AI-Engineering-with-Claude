import uvicorn
from fastapi import FastAPI, HTTPException, Path
from sqlmodel import SQLModel, Field, Session, create_engine, select

from faker import Faker
from loguru import logger
from pydantic import BaseModel, StrictInt
from os import getenv


# Models
class Account(SQLModel, table=True):
    id: str = Field(primary_key=True)
    owner: str
    balance: int = 100000  # Whole USD; opening balance before seed transactions.


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    account_id: str
    type: str  # DEPOSIT or WITHDRAWAL
    amount: int
    merchant: str
    date: str  # YYYY-MM-DD


# Request validation
class AmountRequest(BaseModel):
    amount: StrictInt = Field(gt=0)


# Configuration
TODAY = "2026-11-06"  # Fixed classroom date for new transactions.
DATABASE_URL = getenv("BANK_DATABASE_URL", "sqlite:///nano_bank_simple.db")

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)
db = Session(engine)  # Shared session for sequential, single-user classroom requests.

# Synthetic data
if db.get(Account, "ACC101") is None:
    account = Account(id="ACC101", owner="Alice")
    db.add(account)
    fake = Faker()
    fake.seed_instance(0)
    for month in range(1, 13):
        db.add(Transaction(account_id="ACC101", type="DEPOSIT", amount=5000,
                           merchant="Salary", date=f"2025-{month:02d}-01"))
        db.add(Transaction(account_id="ACC101", type="WITHDRAWAL", amount=180,
                           merchant=fake.company(), date=f"2025-{month:02d}-15"))
        account.balance += 5000 - 180
    db.commit()

app = FastAPI(title="Nano Bank")


def get_account(account_id):
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(404, "Account not found")
    return account


# API Endpoints
@app.post("/accounts/{account_id}/deposit")
def deposit(account_id: str, request: AmountRequest):
    account = get_account(account_id)
    account.balance += request.amount
    db.add(Transaction(account_id=account_id, type="DEPOSIT", amount=request.amount,
                       merchant="Deposit", date=TODAY))
    db.commit()
    logger.info("Deposit: {} USD into {}", request.amount, account.id)
    return {"account_id": account.id, "balance": account.balance}


@app.post("/accounts/{account_id}/withdraw")
def withdraw(account_id: str, request: AmountRequest):
    account = get_account(account_id)
    if request.amount > account.balance:
        raise HTTPException(409, "Insufficient funds")
    account.balance -= request.amount
    db.add(Transaction(account_id=account_id, type="WITHDRAWAL", amount=request.amount,
                       merchant="Withdrawal", date=TODAY))
    db.commit()
    logger.info("Withdrawal: {} USD from {}", request.amount, account.id)
    return {"account_id": account.id, "balance": account.balance}


@app.get("/accounts/{account_id}/statement/{year}/{month}")
def statement(account_id: str, year: int = Path(ge=1), month: int = Path(ge=1, le=12)):
    account = get_account(account_id)
    period = f"{year:04d}-{month:02d}"
    query = select(Transaction).where(
        Transaction.account_id == account_id, Transaction.date.startswith(period)
    ).order_by(Transaction.date, Transaction.id)
    transactions = db.exec(query).all()
    deposits = sum(t.amount for t in transactions if t.type == "DEPOSIT")
    withdrawals = sum(t.amount for t in transactions if t.type == "WITHDRAWAL")
    return {"account_id": account_id, "month": period, "total_deposits": deposits,
            "total_withdrawals": withdrawals, "net_flow": deposits - withdrawals,
            "current_balance": account.balance, "transactions": transactions}


# AI exercises
# Required libraries: litellm & anthropic
def chatbot(message: str):
    from anthropic import Anthropic
    client = Anthropic(api_key=getenv("CLAUDE_API_KEY"))
    client_response = client.messages.create(
        model = "claude-haiku-5-5",
        messages = [{"role": "user", "content": message}],
        max_tokens = 124,
        # or "claude-instant-v1"
    )
    client_response_text = client_response.content[0].text
    return client_response_text
    

def build_chatbot_interface():
    import gradio as gr
    gr.Interface(fn=chatbot, inputs="textbox", outputs="textbox").launch(share = True)

def rag(question: str):
    pass


def agent(query: str):
    pass


if __name__ == "__main__":
    port = 8000
    build_chatbot_interface()
    uvicorn.run(app, port= port, host="0.0.0.0", share= True)

