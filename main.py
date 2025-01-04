from datetime import datetime, timedelta
import json
import os
import psycopg2
from dotenv import load_dotenv
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountLines
from xrpl.models.requests import AccountTx
from xrpl.models.requests import NFTInfo
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.ledger import get_latest_validated_ledger_sequence

cult_amm_addr = 'rwyUJtAL1pAUhSnoNhuWm4edjTanGUyvFH'
cult_cc = '038EABD664A70E5C3B449AADDBECD8811A56A15F'
cult_amm_locked_addr = 'rCULtAKrKbQjk1Tpmg5hkw4dpcf9S9KCs'
cult_actions_db = 'public.cult_actions'
cult_probation_db = 'public.cult_probation'
cult_sent_db = 'public.cult_sent'
cult_daily_record_db = 'public.cult_daily_record'

obey_amm_addr = 'rp3KykYebksKDX1GPdMWTBwjiGjLmTgWxq'
obey_cc = '0357CAA44054A751802BA9128DF6D50915FE88DF'
obey_amm_locked_addr = 'robeyK1nxGh6AKUSSXf3eqyigAWS6Frmw'
obey_actions_db = 'public.obey_actions'
obey_probation_db = 'public.obey_probation'
obey_sent_db = 'public.obey_sent'
obey_daily_record_db = 'public.obey_daily_record'

cult_lp_trustlines = []
cult_transactions = []
obey_lp_trustlines = []
obey_transactions = []

JSON_RPC_URL = "https://s2.ripple.com:51234/"
client = JsonRpcClient(JSON_RPC_URL)

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
LOCAL_PATH = os.getenv('LOCAL_PATH')

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cur = conn.cursor()

def not_locked_addresses(address):
    return address != obey_amm_locked_addr and address != cult_amm_locked_addr

def amm_daily_wallets(address, currency_code, trust_list, db_table, ticker):
    request = AccountLines(
        account=address,
        ledger_index="validated"
    )
    response = client.request(request)
    holders = []
    if response.is_successful():
        with open(LOCAL_PATH +'responses/'+ticker+'Wallets.json', 'w') as json_file:
            json.dump(response.result, json_file, indent=4)
            json_file.close()
        for line in response.result["lines"]:
            if line["currency"] == currency_code:
                cur.execute(
                    "INSERT INTO %s (date, account, balance) VALUES (%s, %s, %s)",
                    (db_table, datetime.now(), line["account"], line["balance"])
                )
                trust_list.append({
                    "address": line["account"],
                    "balance": line["balance"]
                })
        conn.commit()

def amm_daily_transactions(account, trans_list, ticker):
    # Get the latest validated ledger sequence
    current_ledger = get_latest_validated_ledger_sequence(client)

    # Calculate the ledger 24 hours ago (assuming one ledger per ~3-5 seconds, roughly 17,280 ledgers in 24 hours)
    # Note: This is an approximation as ledger creation isn't perfectly uniform
    ledger_24h_ago = current_ledger - (24 * 60 * 60) // 5  # Rough calculation
    account_tx = AccountTx(
        account=account,
        ledger_index_min=ledger_24h_ago,
        ledger_index_max=current_ledger,
        binary=False,  # For human-readable JSON response
        forward=True,  # True for chronological order, False for reverse chronological
    )
    response = client.request(account_tx)
    if response.is_successful():
        with open(LOCAL_PATH +'responses/'+ ticker+'Transactions.json', 'w') as json_file:
            json.dump(response.result, json_file, indent=4)
            json_file.close()
        # transactions = response.result.get("transactions", [])
        # for tx in transactions:
            # find wallet of transaction
            # find type of transaction in or out
            # find amount of xrp, cult/obey, and lp token was exchanged
            # update actions db

            # check transaction for single sided xrp or double sided deposit (+)
            # check transaction for single sided coin deposit (-)
            # check transaction for single sided coin or double sided withdraw (+)
            # check transaction for single sided xrp withdraw (-)
            # if in violation update probation db 

    else:
        print(f"Request failed: {response.status}")
    

# get daily record of wallet holdings
amm_daily_wallets(cult_amm_addr, cult_cc, cult_lp_trustlines, cult_daily_record_db, 'cult')
amm_daily_wallets(obey_amm_addr, obey_cc, obey_lp_trustlines, obey_daily_record_db, 'obey')

# get daily transactions
amm_daily_transactions(cult_amm_addr, cult_transactions, 'cult')
amm_daily_transactions(obey_amm_addr, obey_transactions, 'obey')

# check probation for expired probation
# if wallet is not in probation send obey lp to eligible cult lp holders
# if wallet is not in probation send send cult to eligible obey lp holders

