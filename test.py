from xrpl.models.transactions import Transaction, Payment, TrustSet, AMMDeposit, AMMWithdraw, OfferCreate
import json
from xrpl.account import get_balance
import xrpl
import asyncio
import websockets
import json
from datetime import datetime, timedelta
import json
import os
import asyncio
# import psycopg2
import dotenv
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.account import get_balance
from xrpl.models.transactions import Transaction, Payment, TrustSet, AMMDeposit, AMMWithdraw, OfferCreate
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountLines
from xrpl.models.requests import AccountTx
from xrpl.models.requests import NFTInfo
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.ledger import get_latest_validated_ledger_sequence

cult_token = {
    'token_issuer': 'rCULtAKrKbQjk1Tpmg5hkw4dpcf9S9KCs',
    'cc': '43554C5400000000000000000000000000000000',
    'max': 6969,
    'token_sale_percent_above_market': 1.04,
    'lp_recieved_to_token_percent': 0.5,
    'lp_issuer': 'rwyUJtAL1pAUhSnoNhuWm4edjTanGUyvFH',
    'amm_cc': '038EABD664A70E5C3B449AADDBECD8811A56A15F',
    'amm_max': 100000000000,
    'amm_threshold': 5000
}
obey_token = {
    'token_issuer': 'robeyK1nxGh6AKUSSXf3eqyigAWS6Frmw',
    'cc': '4F42455900000000000000000000000000000000',
    'max': 6.8,
    'token_sale_percent_above_market': 1.04,
    'lp_recieved_to_token_percent': 0.5,
    'lp_issuer': 'rp3KykYebksKDX1GPdMWTBwjiGjLmTgWxq',
    'amm_cc': '0357CAA44054A751802BA9128DF6D50915FE88DF',
    'amm_max': 1000000,
    'amm_threshold': 5000
}
tokens = [cult_token, obey_token]

JSON_RPC_URL = "https://s2.ripple.com:51234/"
client = xrpl.clients.JsonRpcClient(JSON_RPC_URL)

w1 = w1 = Wallet.from_seed('sEdVW6UfrdigkCCw17aVMeSaiERRiNT')


def submit_and_wait(tx):
    try:
        resp = xrpl.transaction.submit_and_wait(tx, client, w1)
        print(f"submit_and_wait resp: {resp}")
        return resp
    except Exception as e:
        err_msg = f'submit_and_wait error: {e}'
        print("submit_and_wait err", e)
    return err_msg


for c in tokens:
    try:
        trust_set = xrpl.models.transactions.TrustSet(
            account=w1.classic_address,
            flags=131072,
            limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                currency=c['cc'],
                issuer=c['token_issuer'],
                value=c['max']
            )
        )
        submit_and_wait(trust_set)

        trust_set = xrpl.models.transactions.TrustSet(
            account=w1.classic_address,
            flags=131072,
            limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                currency=c['amm_cc'],
                issuer=c['lp_issuer'],
                value=c['amm_max']
            )
        )
        submit_and_wait(trust_set)
    except Exception as e:
        print(f'set_trust_line {c['token_issuer']} error: {e}')


# xrp_in_wallet = get_balance('rJhXhcgHvBcsdr2N7aBES9Fj9GkqWEakFm', client)
# print(f"XRP in wallet: {type(xrp_in_wallet)}")
# file_path = "/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_dont_fit/14.json"
# with open(file_path, "r") as file:
#     event = json.load(file)
# print(f"event: {type(event)} {event}")
# payment = Transaction.from_dict(event)
# print(f"Payment: {payment}")
# print(f"Payment amount: {payment.amount}")
# print(f"Payment currency: {payment.amount.currency}")
# print(f"Payment account: {payment.account}")
# print(f"Payment destination: {payment.destination}")
# print(f"Payment fee: {payment.fee}")
# print(f"Payment deliver_min: {payment.deliver_min}")
# print(f"Payment send_max: {payment.send_max}")
                            