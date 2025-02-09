from datetime import datetime, timedelta
import json
import os
import asyncio
# import psycopg2
import dotenv
import xrpl
from xrpl.clients import WebsocketClient, JsonRpcClient
from xrpl.account import get_balance
from xrpl.models.transactions import Payment, TrustSet, AMMDeposit, AMMWithdraw, OfferCreate
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountLines
from xrpl.models.requests import AccountTx
from xrpl.models.requests import NFTInfo
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.ledger import get_latest_validated_ledger_sequence
dotenv.load_dotenv()

# cult lp 8EAB...15F
cult_token = {
    'addr': 'rCULtAKrKbQjk1Tpmg5hkw4dpcf9S9KCs',
    'cc': '43554C5400000000000000000000000000000000',
    'max': 6800,
    'token_sale_percent': 0.04,
    'amm_addr':'rwyUJtAL1pAUhSnoNhuWm4edjTanGUyvFH',
    'amm_cc': '038EABD664A70E5C3B449AADDBECD8811A56A15F',
    'amm_max': 1000000,
    'amm_threshold': 5000
}
obey_token = {
    'addr': 'robeyK1nxGh6AKUSSXf3eqyigAWS6Frmw',
    'cc': '4F42455900000000000000000000000000000000',
    'max': 6.8,
    'token_sale_percent': 0.04,
    'amm_addr':'rp3KykYebksKDX1GPdMWTBwjiGjLmTgWxq',
    'amm_cc': '0357CAA44054A751802BA9128DF6D50915FE88DF',
    'amm_max': 1000000,
    'amm_threshold': 5000
}
tokens = [cult_token, obey_token]
ccList = [cult_token['cc'], obey_token['cc']]
ccAmmList = [cult_token['amm_cc'], obey_token['amm_cc']]
rewards_from_wallet = 'rD56CsTcywRJqtcxJEyJ2QSSY7ZiBZJPzym'

xrp_to_cold_wallet_percent = 0.02
cold_wallet = 'rJhXhcgHvBcsdr2N7aBES9Fj9GkqWEakFm'


TEST_JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
TEST_WS_URL = "wss://s.altnet.rippletest.net:51233" 
TEST_SEED = "sEdViCggFcoanFYa7XcoqXDKqMszySq"

JSON_RPC_URL = "https://s2.ripple.com:51234/"
WS_URL = "wss://s2.ripple.com:51233" 
JSON_RPC_URL = "https://s2.ripple.com:51234/"

# client = JsonRpcClient(JSON_RPC_URL)

# load_dotenv()

# DB_NAME = os.getenv('DB_NAME')
# DB_USER = os.getenv('DB_USER')
# DB_PASSWORD = os.getenv('DB_PASSWORD')
# DB_HOST = os.getenv('DB_HOST')
# LOCAL_PATH = os.getenv('LOCAL_PATH')

# conn = psycopg2.connect(
#     dbname=DB_NAME,
#     user=DB_USER,
#     password=DB_PASSWORD,
#     host=DB_HOST
# )
# cur = conn.cursor()
NUM = os.getenv('MAIN_NUM')
num_list = NUM.split()


def create_wallet_from_mnemonic_or_seed(mnemonic_or_seed):
    w1 = Wallet.from_seed(mnemonic_or_seed)
    print(w1)
    return w1

def create_wallet():
    w1 = Wallet.create()
    print(w1)
    print(w1.seed)
    print(w1.public_key)
    print(w1.private_key)
    return w1


def set_trust_line():
    for c in tokens:
        try:
            trust_set = xrpl.models.transactions.TrustSet(
                account=w1.classic_address,
                limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                    currency=c['cc'],
                    issuer=c['addr'],
                    value=c['max']
                )
            )
            submit_and_wait(trust_set)
        except Exception as e:
            print(f'set_trust_line {c['addr']} error: {e}')

    return trust_set

def submit_and_wait(transaction):
    try:
        return xrpl.transaction.submit_and_wait(transaction, client, w1)
    except Exception as e:
        print(f'submit_and_wait error: {e}')

def send_xrp_transaction_builder(xrp):
    # try:
    #     return xrpl.models.transactions.Payment(
    #         account=w1.classic_address,
    #         destination=cold_wallet,
    #         amount=xrpl.utils.xrp_to_drops(xrp)
    #     )
    # except Exception as e:
    #     print(f'send_xrp_transaction_builder error: {e}')
    #     return 'error'
    return 'testing'

def handle_transaction(amount, event):
    tx = event["transaction"]
    print(f'handle_transaction: {tx}')
    # Recieved XRP
    if tx["TransactionType"] == "Payment" and tx["Destination"] == w1.classic_address:
        try:
            # TODO Check what was sold
            sold_currency_cc = ''
            sold_currency_amm_cc = ''
            sold_currency_issuer = ''
            amount = tx["Amount"]
            print(f"Received {amount} of XRP for the sale of {sold_currency_cc}")
        except Exception as e:
            print(f'Recieved XRP Check what was sold error {e}')

        try:
            # Send 2% to cold_wallet
            send_amount = int(amount * 0.02)
            deposit_amount = amount - send_amount
            
            payment_tx = Payment(
                account=w1.classic_address,
                destination=cold_wallet,
                amount=send_amount
            )
            submit_and_wait(payment_tx)
        except Exception as e:
            print(f'Recieved XRP Send 2% to cold_wallet error {e}')
        
        try:
            # Deposit remaining XRP into AMM Pool
            amm_tx = AMMDeposit(
                account=w1.classic_address,
                asset={"currency": sold_currency_amm_cc, "issuer": sold_currency_issuer},
                amount=str(deposit_amount)
            )
            submit_and_wait(amm_tx)
            print(f"Deposited {deposit_amount / 1_000_000} XRP into AMM pool")
        except Exception as e:
            print(f'Recieved XRP Deposit remaining XRP into AMM Pool error {e}')

    # Recieved LP
    elif tx["TransactionType"] == "Payment" and tx["Destination"] == w1.classic_address and tx.get("Amount", {}).get("currency") in ccAmmList:
        try:
            for c in tokens:
                if tx.get("Amount", {}).get("currency") == c['amm_cc']:
                    recieved_lp_cc = c['amm_cc']
                    recieved_currency_cc = c['cc']
                    recieved_currency_issuer = c['addr'] # is this thee issuer?
                    recieved_lp_amount = int(tx["Amount"]["value"])
                    recieved_lp_threshold = c['amm_max']
            print(f"Received {recieved_lp_amount} of {recieved_lp_cc} LP Token ")
        except Exception as e:
            print(f'Recieved LP Check what was sold error {e}')
        
        try:
            # Swap 50% of recieved_lp for token
            swap_amount = int(recieved_lp_amount * 0.75)
            amm_withdraw = AMMWithdraw(
                account=w1.classic_address,
                asset = {"currency": recieved_currency_cc, "issuer": recieved_currency_issuer},
                asset2 = 'XRP',
                amount2 = None,
                lp_token_in = swap_amount,
            )
            submit_and_wait(amm_withdraw)
            print(f"Swapped {swap_amount} LP1 for {recieved_currency_cc}")
        except Exception as e:
            print(f'Recieved LP Swap 75% of recieved_lp for token error {e}')
        
        try:
            # If LP1 balance > threshold, send 25% to cold_wallet
            lp1_balance = get_balance(w1.classic_address, client, recieved_lp_cc)
            if lp1_balance > recieved_lp_threshold:
                send_lp1 = int(lp1_balance * 0.25)
                lp1_payment = Payment(
                    account=w1.classic_address,
                    destination=cold_wallet,
                    amount={"currency": recieved_lp_cc, "issuer": recieved_currency_issuer, "value": str(send_lp1)}
                )
                submit_and_wait(lp1_payment)
                print(f"Sent {send_lp1} LP1 to cold_wallet")
        except Exception as e:
            print(f'Recieved LP Send 25% to cold_wallet error {e}')
    
    # Recieved Token
    elif tx["TransactionType"] == "Payment" and tx["Destination"] == w1.classic_address and tx.get("Amount", {}).get("currency") in ccList:
        print(f"Received T1 tokens")
        try:
            for c in tokens:
                if tx.get("Amount", {}).get("currency") == c['cc']:
                    recieved_currency_cc = c['cc']
                    recieved_currency_issuer = c['addr'] # is this thee issuer?
                    recieved_amount = int(tx["Amount"]["value"])
            print(f"Received {recieved_amount} of {recieved_currency_cc} Token ")
        except Exception as e:
            print(f'Recieved Token Check what was sold error {e}')
        
        # Make sell order for 4% above market
        try:
            offer_tx = OfferCreate(
                account=w1.classic_address,
                taker_pays={"currency": recieved_currency_cc, "issuer": recieved_currency_issuer, "value": str(recieved_amount)},
                taker_gets=str(int(recieved_amount * 1.04))  # Selling at 4% above market
            )
            submit_and_wait(offer_tx)
            print(f"Set sell order for {recieved_amount} T1 at 4% over market price")
        except Exception as e:
            print(f'Recieved Token sell order for 4% above market error {e}')

def monitor_wallet():        
    with WebsocketClient(WS_URL) as ws:
        subscribe_msg = {
            "command": "subscribe",
            "accounts": [w1.classic_address]
        }
        print(f"subscribe_msg: {subscribe_msg}")
        try:
            ws.send(json.dumps(subscribe_msg))
        except Exception as e:
            print(f"Websocket error: {e}")
        # for message in client:
        #     print(f"WS Message: {message}")
        print(f"Listening for transactions on {w1.classic_address}")
        while True:
            print('monitor_wallet')
            try:
                for message in ws:
                    print(f"WS Message: type({message}): {message}")
                # response = ws.recv()
                # print(f"WS response: {response}")
                # event = json.loads(message)
                    if "transaction" in message:
                        handle_transaction(message)
            except Exception as e:
                print(f"Error: {e}")

# def main():
#     monitor_wallet()

if __name__ == "__main__":
    client = xrpl.clients.JsonRpcClient(JSON_RPC_URL)
    # create_wallet()
    # w1 = create_wallet_from_mnemonic_or_seed(TEST_SEED)
    w1 = Wallet.from_secret_numbers(num_list)
    monitor_wallet()
    # asyncio.run(main())
