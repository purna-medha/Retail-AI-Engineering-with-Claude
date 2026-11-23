import httpx

url = "http://127.0.0.1:8000/accounts/ACC101"

# In Postman, use the same HTTP method, URL, and JSON body as these calls.

# January statement
# curl http://127.0.0.1:8000/accounts/ACC101/statement/2025/1
print(httpx.get(url = f"{url}/statement/2025/1").json())

# Deposit 500 USD
# curl -X POST http://127.0.0.1:8000/accounts/ACC101/deposit \
#   -H 'Content-Type: application/json' \
#   -d '{"amount": 500}'
response = httpx.post(
    url  = f"{url}/deposit",
    json = {"amount": 500},
)
print(response.json())

# Withdraw 100 USD
# curl -X POST http://127.0.0.1:8000/accounts/ACC101/withdraw \
#   -H 'Content-Type: application/json' \
#   -d '{"amount": 100}'
response = httpx.post(
    url  = f"{url}/withdraw",
    json = {"amount": 100},
)
print(response.json())

# Updated statement (new transactions use the fixed date 2026-11-06)
# curl http://127.0.0.1:8000/accounts/ACC101/statement/2026/11
print(httpx.get(f"{url}/statement/2026/11").json())
