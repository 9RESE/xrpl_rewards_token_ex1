import xrpl
from xrpl.wallet import Wallet
import os
import dotenv
dotenv.load_dotenv()

wallet_name = 'CULT_OBEY'
cult_token = {
    'token_issuer': 'rCULtAKrKbQjk1Tpmg5hkw4dpcf9S9KCs',
    'cc': '43554C5400000000000000000000000000000000',
    'max': 6969,
    'lp_issuer': 'rwyUJtAL1pAUhSnoNhuWm4edjTanGUyvFH',
    'amm_cc': '038EABD664A70E5C3B449AADDBECD8811A56A15F',
    'amm_max': 100000000000
}
obey_token = {
    'token_issuer': 'robeyK1nxGh6AKUSSXf3eqyigAWS6Frmw',
    'cc': '4F42455900000000000000000000000000000000',
    'max': 6.8,
    'lp_issuer': 'rp3KykYebksKDX1GPdMWTBwjiGjLmTgWxq',
    'amm_cc': '0357CAA44054A751802BA9128DF6D50915FE88DF',
    'amm_max': 1000000
}
tokens = [cult_token, obey_token]

JSON_RPC_URL = "https://s2.ripple.com:51234/"
client = xrpl.clients.JsonRpcClient(JSON_RPC_URL)

def submit_and_wait(tx):
    try:
        resp = xrpl.transaction.submit_and_wait(tx, client, w1)
        print(f"submit_and_wait resp: {resp}")
        return resp
    except Exception as e:
        err_msg = f'submit_and_wait error: {e}'
        print("submit_and_wait err", e)
    return err_msg

WALLET_SEED = os.getenv(f'{wallet_name}_SEED')
w1 = Wallet.from_seed(WALLET_SEED)
for c in tokens:
    try:
        trust_set = xrpl.models.transactions.TrustSet(
            account=w1.classic_address,
            flags=131072, # disables RIPPELING
            limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                currency=c['cc'],
                issuer=c['token_issuer'],
                value=c['max']
            )
        )
        submit_and_wait(trust_set)

        trust_set = xrpl.models.transactions.TrustSet(
            account=w1.classic_address,
            flags=131072, # disables RIPPELING
            limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                currency=c['amm_cc'],
                issuer=c['lp_issuer'],
                value=c['amm_max']
            )
        )
        submit_and_wait(trust_set)
    except Exception as e:
        print(f'set_trust_line {c['token_issuer']} error: {e}')
############## Now send Cult LP tokens and Obey tokens to the wallet {w1.classic_address} then start the m3.py script.##############
