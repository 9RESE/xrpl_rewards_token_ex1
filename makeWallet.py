import xrpl
from xrpl.wallet import Wallet
import os
import dotenv
dotenv.load_dotenv()

############## User Defined Variable ##############
wallet_name = 'CULT_OBEY'

JSON_RPC_URL = "https://s2.ripple.com:51234/"
client = xrpl.clients.JsonRpcClient(JSON_RPC_URL)

w1 = Wallet.create()
print(f'w1: {w1}')
with open('.env', 'a') as f:
    f.write(f'{wallet_name}_SEED={w1.seed}\n{wallet_name}_ADDR={w1.classic_address}\n{wallet_name}_PUKEY={w1.public_key}\n{wallet_name}_PRKEY={w1.private_key}\n')
############## Now seed XRP to the wallet {w1.classic_address} ##############
