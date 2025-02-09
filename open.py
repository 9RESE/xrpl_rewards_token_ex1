import xrpl
import asyncio
import json
from xrpl.wallet import Wallet
from xrpl.clients import WebsocketClient, JsonRpcClient
from xrpl.account import get_balance
# from xrpl.transactions import prepare_transaction, send_reliable_submission
from xrpl.models.transactions import Payment, TrustSet, AMMDeposit, AMMWithdraw, OfferCreate
from xrpl.ledger import get_latest_validated_ledger_sequence

# Constants
RPC_URL = "https://s.altnet.rippletest.net:51234"  # Change for mainnet
WS_URL = "wss://s.altnet.rippletest.net:51233"    # Change for mainnet

# Initialize JSON-RPC client
client = JsonRpcClient(RPC_URL)

# Wallet setup
W1 = Wallet.create()  # Generates a new wallet
W2 = "rEXAMPLECOLDWALLET"  # Replace with actual cold wallet address

# Token information
T1_ISSUER = "rEXAMPLETOKENISSUER"
T1_CURRENCY = "T1"
LP1_CURRENCY = "LP1"
LP1_THRESHOLD = 100000  # Threshold for LP1 tokens

async def set_trust_lines():
    """Set trust lines for T1 and LP1 in W1."""
    for currency in [T1_CURRENCY, LP1_CURRENCY]:
        trust_set_tx = TrustSet(
            account=W1.classic_address,
            limit_amount={
                "currency": currency,
                "issuer": T1_ISSUER,
                "value": "1000000000"  # Large trust line
            }
        )
        prepared_tx = await prepare_transaction(trust_set_tx, client, W1)
        send_reliable_submission(prepared_tx, client)
        print(f"Trust line set for {currency}")

async def handle_transaction(event):
    """Handle incoming transactions to W1."""
    tx = event["transaction"]
    if tx["TransactionType"] == "Payment" and tx["Destination"] == W1.classic_address:
        amount = int(tx["Amount"])
        print(f"Received {amount / 1_000_000} XRP")
        
        # Send 2% to W2
        send_amount = int(amount * 0.02)
        deposit_amount = amount - send_amount
        
        payment_tx = Payment(
            account=W1.classic_address,
            destination=W2,
            amount=str(send_amount)
        )
        prepared_tx = await prepare_transaction(payment_tx, client, W1)
        send_reliable_submission(prepared_tx, client)
        print(f"Sent {send_amount / 1_000_000} XRP to W2")
        
        # Deposit remaining XRP into AMM Pool
        amm_tx = AMMDeposit(
            account=W1.classic_address,
            asset={"currency": T1_CURRENCY, "issuer": T1_ISSUER},
            amount=str(deposit_amount)
        )
        prepared_tx = await prepare_transaction(amm_tx, client, W1)
        send_reliable_submission(prepared_tx, client)
        print(f"Deposited {deposit_amount / 1_000_000} XRP into AMM pool")
    
    elif tx["TransactionType"] == "Payment" and tx["Destination"] == W1.classic_address and tx.get("Amount", {}).get("currency") == LP1_CURRENCY:
        print(f"Received LP1 tokens")
        
        # Swap 5% of LP1 for T1
        lp1_balance = get_balance(W1.classic_address, client, LP1_CURRENCY)
        swap_amount = int(lp1_balance * 0.05)
        amm_withdraw = AMMWithdraw(
            account=W1.classic_address,
            asset={"currency": LP1_CURRENCY, "issuer": T1_ISSUER},
            amount=str(swap_amount)
        )
        prepared_tx = await prepare_transaction(amm_withdraw, client, W1)
        send_reliable_submission(prepared_tx, client)
        print(f"Swapped {swap_amount} LP1 for T1")
        
        # If LP1 balance > threshold, send 25% to W2
        if lp1_balance > LP1_THRESHOLD:
            send_lp1 = int(lp1_balance * 0.25)
            lp1_payment = Payment(
                account=W1.classic_address,
                destination=W2,
                amount={"currency": LP1_CURRENCY, "issuer": T1_ISSUER, "value": str(send_lp1)}
            )
            prepared_tx = await prepare_transaction(lp1_payment, client, W1)
            send_reliable_submission(prepared_tx, client)
            print(f"Sent {send_lp1} LP1 to W2")
    
    elif tx["TransactionType"] == "Payment" and tx["Destination"] == W1.classic_address and tx.get("Amount", {}).get("currency") == T1_CURRENCY:
        print(f"Received T1 tokens")
        t1_balance = get_balance(W1.classic_address, client, T1_CURRENCY)
        offer_tx = OfferCreate(
            account=W1.classic_address,
            taker_pays={"currency": T1_CURRENCY, "issuer": T1_ISSUER, "value": str(t1_balance)},
            taker_gets=str(int(t1_balance * 1.04))  # Selling at 4% above market
        )
        prepared_tx = await prepare_transaction(offer_tx, client, W1)
        send_reliable_submission(prepared_tx, client)
        print(f"Set sell order for {t1_balance} T1 at 4% over market price")

async def monitor_wallet():
    """Monitor wallet W1 for deposits via WebSocket."""
    async with xrpl.asyncio.clients.AsyncWebsocketClient(WS_URL) as ws:
            # await client.on_connected()
        subscribe_msg = {
            "command": "subscribe",
            "accounts": [W1.classic_address]
        }
        await ws.send(json.dumps(subscribe_msg))
        print(f"Listening for transactions on {W1.classic_address}")
        
        while True:
            try:
                response = await ws.recv()
                event = json.loads(response)
                if "transaction" in event:
                    await handle_transaction(event)
            except Exception as e:
                print(f"Error: {e}")

async def main():
    await set_trust_lines()
    await monitor_wallet()

if __name__ == "__main__":
    asyncio.run(main())
