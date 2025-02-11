import asyncio
import websockets
import json
from datetime import datetime
import json
import os
import psycopg2
import asyncio
import dotenv
import xrpl
from xrpl.models.transactions import Payment, AMMDeposit, AMMWithdraw, OfferCreate
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait

dotenv.load_dotenv()

database = True
DB_NAME = "tk_massager"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

############## User Defined Variables ##############
xrp_to_cold_wallet_percent = 0.02 # percentage of XRP to send to cold storage
xrp_threshold = 10000000 # total amount of XRP to hold before sending some to cold storage

#Tokens to massage
cult_token = {
    'token_name': 'CULT',
    'token_issuer': 'rCULtAKrKbQjk1Tpmg5hkw4dpcf9S9KCs',
    'cc': '43554C5400000000000000000000000000000000',
    'token_sale_percent_above_market': 1.25,              # % above markey ############## User Defined Variable ##############
    'lp_name': 'CULT_LP',
    'lp_recieved_to_token_percent': 0.5,                  # % ############## User Defined Variable ##############
    'lp_issuer': 'rwyUJtAL1pAUhSnoNhuWm4edjTanGUyvFH',
    'amm_cc': '038EABD664A70E5C3B449AADDBECD8811A56A15F',
    'amm_threshold': 5000 ,                                 ############## User Defined Variable ############## total amount of lp tokens to hold before sending some to cold storage
    'amm_percent_to_cold': .25                              # % ############## User Defined Variable ##############
}
obey_token = {
    'token_name': 'OBEY',
    'token_issuer': 'robeyK1nxGh6AKUSSXf3eqyigAWS6Frmw',
    'cc': '4F42455900000000000000000000000000000000',
    'token_sale_percent_above_market': 1.25,               # % above markey ############## User Defined Variable ##############
    'lp_name': 'OBEY_LP',
    'lp_recieved_to_token_percent': 0.5,                   # % ############## User Defined Variable ##############
    'lp_issuer': 'rp3KykYebksKDX1GPdMWTBwjiGjLmTgWxq',
    'amm_cc': '0357CAA44054A751802BA9128DF6D50915FE88DF',
    'amm_threshold': 5000,                                  ############## User Defined Variable ############## total amount of lp tokens to hold before sending some to cold storage
    'amm_percent_to_cold': .25                              # % ############## User Defined Variable ##############
}
tokens = [cult_token, obey_token]
cult_obey_cc_list = [cult_token['cc'], obey_token['cc']]
cult_obey_cc_amm_list = [cult_token['amm_cc'], obey_token['amm_cc']]
cc_list = [cult_token['cc'], obey_token['cc']]
amm_list = [cult_token['amm_cc'], obey_token['amm_cc']]

# TEST_JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
# TEST_WS_URL = "wss://s.altnet.rippletest.net:51233" 
# TEST_SEED = "sEdViCggFcoanFYa7XcoqXDKqMszySq"

JSON_RPC_URL = "https://s2.ripple.com:51234/"
WS_URL = "wss://s2.ripple.com:51233" 
JSON_RPC_URL = "https://s2.ripple.com:51234/"

COLD_NUM = os.getenv('COLD_NUM') # XUMM Wallets
COLD_ADDR = os.getenv('COLD_ADDR') # XUMM Wallets
CULT_OBEY_SEED = os.getenv('CULT_OBEY_SEED') # Paper Wallets
CULT_OBEY_ADDR = os.getenv('CULT_OBEY_ADDR') # Paper Wallets

async def write_error_to_file(event, err_msg):
    file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    if not os.path.exists(f"{working_dir}/err/{file_name}"):
        os.makedirs(f"{working_dir}/err/{file_name}")
    with open(f"{working_dir}/err/{file_name}/{file_name}.json", "w")  as f:
                        json.dump(event, f, indent=4)
                        f.close()
    with open(f"{working_dir}/err/{file_name}/{file_name}.txt", "w")  as f2:
                        f2.write(err_msg)
                        f2.close()
    if database:
        q = "INSERT INTO tk_massager (time, action, err) VALUES (%%s, %%s, %%s)"
        cursor.execute(q, (event['transaction']['date'], 'ERR', err_msg))
        conn.commit()

async def get_xrp_holdings(w1, ws):
    try:
        resp = await api_request({
            "id": 2,
            "command": "account_info",
            "account": w1.classic_address,
            "ledger_index": "current",
            "queue": True
        }, ws)
        xrp = resp['result']['account_data']['Balance']
        print(f"XRP in wallet: {type(xrp)} {xrp}")
        return xrp
    except Exception as e:
        err_msg = f'Check holdings xrp error {e}'
        print(err_msg)
        await write_error_to_file('xrp', err_msg)

async def get_holdings(cc, w1, ws):
    try:
        response = await api_request({
            "id": 1,
            "command": "account_lines",
            "account": w1.classic_address,
            }, ws)
        token_balance = None
        for line in response['result']["lines"]:
            if line["currency"] == cc:
                token_balance = line["balance"]
                break
        return token_balance
    except Exception as e:
        err_msg = f'Check holdings {cc} error {e}'
        print(err_msg)
        await write_error_to_file(cc, err_msg)

async def recieved_xrp(event, w1, ws):
    print('Recieved XRP')
    try:
        xrp_in_wallet = get_xrp_holdings(w1, ws)
        print(f"XRP in wallet: {type(xrp_in_wallet)} {xrp_in_wallet}")
        # Send XRP to COLD_ADDR
        if xrp_in_wallet > xrp_threshold:
            send_amount = xrp_in_wallet * xrp_to_cold_wallet_percent - 15
            print(f"send xrp: {send_amount}")
            after_cold_deposit_amount = xrp_in_wallet - send_amount
            print(f"after_cold_deposit_amount: {after_cold_deposit_amount}")
            lp_deposit_amount = after_cold_deposit_amount/2 - 15
            print(f"lp_deposit_amount: {lp_deposit_amount}")
            try:
                payment_tx = Payment(
                    account=w1.classic_address,
                    destination=COLD_ADDR,
                    amount=str(send_amount)
                )
                resp = await submit_and_wait(payment_tx, client, w1)
                msg = f'Sent XRP to COLD_ADDR. resp = {resp}'
                print(f'Sent XRP to COLD_ADDR. resp = {resp}')
                if database:
                    q = "INSERT INTO tk_massager (time, action, message, xrp_amount) VALUES (%%s, %%s, %%s, %%s)"
                    cursor.execute(q, (event['transaction']['date'], 'XRP to COLD_ADDR', msg, send_amount))
            except Exception as e:
                err_msg = f'Recieved XRP Send to COLD_ADDR error {e}'
                print(err_msg)
                await write_error_to_file(event, err_msg)

            try:
                for c in tokens:
                    lp_before = await get_holdings(c['amm_cc'], w1, ws)
                    amm_tx = AMMDeposit(
                        account=w1.classic_address,
                        asset={"currency": 'XRP'},
                        asset2={"currency": c['cc'], "issuer": c['token_issuer']},
                        amount=str(lp_deposit_amount),
                        amount2=None,
                        flags=524288
                    )
                    resp = await submit_and_wait(amm_tx, client, w1)
                    msg = f"Deposited {lp_deposit_amount} Drops into {c['cc']} AMM pool. resp = {resp}"
                    print(msg)  
                    lp_after = await get_holdings(c['amm_cc'], w1, ws)
                    new_lp = lp_after - lp_before
                    if database:
                        q = "INSERT INTO tk_massager (time, action, message, xrp_amount, lp_amount, lp_token_amount, lp_token, lp_token_cc, lp_token_issuer) VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)"
                        cursor.execute(q, (event['transaction']['date'], 'AMMDeposit', msg, lp_deposit_amount, new_lp, c['lp_name'], c['amm_cc'], c['lp_issuer']))
                        conn.commit()
            except Exception as e:
                err_msg = f'Recieved XRP Send to AMM pool error {e}'
                print(err_msg)
                await write_error_to_file(event, err_msg)
    except Exception as e:
        err_msg = f'Recieved XRP Send error {e}'
        print(err_msg)
        await write_error_to_file(event, err_msg)

async def recieved_lp(event, delivered_currency, delivered_issuer, delivered_value, w1, ws):
    print(f"Received LP", delivered_currency, delivered_issuer, delivered_value)
    recieved_lp_amount = delivered_value
    recieved_lp_issuer = delivered_issuer 
    recieved_lp_cc = delivered_currency
    for c in tokens:
        if delivered_currency == c['amm_cc']:
            token_dict = c    
    try:
        # Swap % of recieved_lp for token
        lp_before = await get_holdings(recieved_lp_cc, w1, ws)
        token_before = await get_holdings(c['cc'], w1, ws)
        swap_amount = int(recieved_lp_amount * token_dict['lp_recieved_to_token_percent'])
        amm_withdraw = AMMWithdraw(
            account=w1.classic_address,
            asset = {"currency": token_dict['cc'], "issuer": token_dict['token_issuer']},
            asset2 = 'XRP',
            amount2 = None,
            lp_token_in = swap_amount,
            flags = 262144
        )
        resp = await submit_and_wait(amm_withdraw, client, w1)
        msg = f"Swapped {swap_amount} LP1 for {token_dict['cc']}. resp = {resp}"
        print(msg)
        lp_after = await get_holdings(recieved_lp_cc, w1, ws)
        token_after = await get_holdings(c['cc'], w1, ws)
        new_lp = lp_after - lp_before
        new_token = token_after - token_before
        if database:
            q = "INSERT INTO tk_massager (time, action, message, token_amount, token, token_cc, token_issuer, lp_amount, lp_token, lp_token_cc, lp_token_issuer) VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)"
            cursor.execute(q, (event['transaction']['date'], 'AMMWithdraw', msg, new_token, c['token_name'], c['cc'], c['token_issuer'], new_lp, c['lp_name'], c['amm_cc'], c['lp_issuer']))

    except Exception as e:
        err_msg = f'Recieved LP Swap {token_dict['lp_recieved_to_token_percent']} of recieved_lp for token error {e}'
        print(err_msg)
        await write_error_to_file(event, err_msg)

    try:
        # If LP1 balance > threshold, send 25% to COLD_ADDR
        if lp_after > token_dict['amm_threshold']:
            send_lp1 = int(lp_after * 0.25)
            lp1_payment = Payment(
                account=w1.classic_address,
                destination=COLD_ADDR,
                amount={"currency": recieved_lp_cc, "issuer": recieved_lp_issuer, "value": str(send_lp1)}
            )
            resp = await submit_and_wait(lp1_payment, client, w1)
            msg = f"Sent {send_lp1} LP1 to COLD_ADDR. resp = {resp}"
            print(msg)
            if database:
                q = "INSERT INTO tk_massager (time, action, message, lp_amount, lp_token, lp_token_cc, lp_token_issuer) VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s)"
                cursor.execute(q, (event['transaction']['date'], 'LP to COLD', msg, send_lp1, c['lp_name'], c['amm_cc'], c['lp_issuer']))
                conn.commit()
    except Exception as e:
        err_msg = f'Recieved LP Send 25% to COLD_ADDR error {e}'
        print(err_msg)
        await write_error_to_file(event, err_msg)

async def recieved_token(event, delivered_currency, delivered_issuer, delivered_value, w1, ws):
    print(f"Received Tokens ", delivered_currency, delivered_issuer, delivered_value)
    recieved_currency_cc = delivered_currency
    recieved_currency_issuer = delivered_issuer
    recieved_amount = float(delivered_value)
    try:
        for c in tokens:
            if delivered_currency == c['cc']:
                token_dict = c
    except Exception as e:
        err_msg = f'Recieved Token Check what was sold error {e}'
        print(err_msg)
        await write_error_to_file(event, err_msg)
    
    # Make sell order for % above market
    try:
        current_market_price = await get_last_exchange_price(recieved_currency_issuer, ws)
        print(f"current_market_price = {current_market_price}")
        sale_price = int(current_market_price * token_dict['token_sale_percent_above_market'])
        recieve_xrp = int(sale_price*recieved_amount)
        print(f"sale_price {sale_price} ")
        print(f"recieve_xrp {recieve_xrp} ")
        offer_tx = OfferCreate(
            account=w1.classic_address,
            taker_gets={"currency": recieved_currency_cc, "issuer": recieved_currency_issuer, "value": str(recieved_amount)},
            taker_pays=str(recieve_xrp)  # Selling at token_sale_percent_above_market% above market
        )
        resp = await submit_and_wait(offer_tx, client, w1)
        msg = f"Set sell order for {recieved_amount} of {recieved_currency_cc} for {str(sale_price)}% over market price. resp = {resp}"
        print(msg)
        if database:
            q = "INSERT INTO tk_massager (time, action, message, xrp_amount, token_amount, token, token_cc, token_issuer) VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)"
            cursor.execute(q, (event['transaction']['date'], 'OfferCreate', msg, recieve_xrp, recieved_amount, token_dict['token_name'], recieved_currency_cc, recieved_currency_issuer))
            conn.commit()

    except Exception as e:
        err_msg = f'Recieved Token sell order for {token_dict['token_sale_percent_above_market']} above market error  {e}'
        print(err_msg)
        await write_error_to_file(event, err_msg)

async def get_last_exchange_price(token_issuer, ws):
    last_price = -1
    try:
        print(f"get_last_exchange_price {token_issuer}")
        resp = await api_request({
            "id": 2,
            "command": "account_tx",
            "account": token_issuer,
            "ledger_index_min": -1,
            "ledger_index_max": -1,
            "limit": 100,
            "api_version": 2}, ws)
        ledger_data_index = resp.result["ledger_index"]
    except Exception as e:
        err_msg = f'get_last_exchange_price 1 error {e}'
        print(err_msg)
        await write_error_to_file('xrp', err_msg)

    try:
        while True:
            for tx in resp['transactions']:
                tx_meta = tx['meta']
                tx_json = tx['tx_json']
                if tx_json['TransactionType'] == "Payment" and tx_json['Account'] != 'rD56CsTcywRJqtcxJEyJ2QSY7ZiBZJPzym' and tx_json['Account'] == tx_json['Destination']:
                    if 'DeliverMax' in tx_json: #Market Sale
                        # print(f"Market Sale 1")
                        if 'currency' in tx_json['DeliverMax']: #Market Sale
                            # print(f"Market Sale 2")
                            token_amount = float(tx_meta['delivered_amount']['value'])
                            for node in tx_meta['AffectedNodes']:
                                # print(f"Market Sale 3")
                                if 'ModifiedNode' in node:
                                    # print(f"Market Sale 4")
                                    if 'FinalFields' in node['ModifiedNode']:
                                        # print(f"Market Sale 5")
                                        if 'Account' in node['ModifiedNode']['FinalFields'] and 'Balance' in node['ModifiedNode']['FinalFields']:
                                            print(f"Market Sale {tx}")
                                            xrp_final_balance = float(node['ModifiedNode']['FinalFields']['Balance'])
                                            xrp_prev_balance = float(node['ModifiedNode']['PreviousFields']['Balance'])
                                            xrp_amount = xrp_final_balance - xrp_prev_balance
                                            last_price = abs(int(xrp_amount / token_amount))
                                            return last_price
                    elif tx_json['TransactionType'] == "Payment" and tx_json['Account'] != 'rD56CsTcywRJqtcxJEyJ2QSY7ZiBZJPzym' and tx_json['Account'] != tx_json['Destination']: # Market Buy
                        print(f"Market Buy {tx}")
                        xrp_amount = float(tx_meta['delivered_amount']) # 77342
                        token_amount = float(tx_json['SendMax']['value']) # 0.00001282794438197
                        last_price = abs(int(xrp_amount / token_amount))
                        return last_price
                    
            if "marker" not in resp:
                print(f"get_last_exchange_price marker not in resp")
                break
            resp = await api_request({
            "id": 2,
            "command": "account_tx",
            "account": token_issuer,
            "limit": 100,
            "api_version": 2,
            "ledger_index": ledger_data_index,
            "marker": resp["marker"]
            }, ws).result
                
        return last_price
    except Exception as e:
        err_msg = f'get_last_exchange_price 2 error {e}'
        print(err_msg)
        await write_error_to_file('xrp', err_msg)

# Handles incoming messages
async def handler(websocket):
    message = await websocket.recv()
    return message

# Use this to send API requests
async def api_request(options, websocket):
    try:
        await websocket.send(json.dumps(options))
        message = await websocket.recv()
        # print(f"api_request message: {message}")
        return json.loads(message)
    except Exception as e:
        return e

async def run():
    if database:
        await create_tables()
    # Opens connection to ripple websocket
    count = 1
    async for ws in websockets.connect('wss://s2.ripple.com:51233'):
        try:
            subscribe_msg = {
                "command": "subscribe",
                "accounts": wallet_addrs
            }
            await ws.send(json.dumps(subscribe_msg))
            print(f"Listening for transactions on {wallet_addrs}")
            while True:
                try:
                    response = await ws.recv()
                    event = json.loads(response)
                    if "transaction" in event:
                        tx = event["transaction"]
                        if tx["TransactionType"] == "Payment" and tx["Destination"] in wallet_addrs:
                            print(f"Event Fits 1")
                            try:
                                delivered_currency = event['meta']['delivered_amount']['currency']
                                delivered_issuer = event['meta']['delivered_amount']['issuer']
                                delivered_value = float(event['meta']['delivered_amount']['value'])
                                for c in wallets:
                                    if tx["Destination"] == c.classic_address:
                                        wallet = c
                                if delivered_currency in cc_list:
                                    await recieved_token(event, delivered_currency, delivered_issuer, delivered_value, wallet, ws)
                                elif delivered_currency in amm_list:
                                    await recieved_lp(event, delivered_currency, delivered_issuer, delivered_value, wallet, ws)
                            except:
                                delivered_currency = 'xrp'
                                delivered_issuer = None
                                delivered_value = float(event['meta']['delivered_amount'])
                                for c in wallets:
                                    if tx["Destination"] == c.classic_address:
                                        wallet = c
                                await recieved_xrp(event, wallet, ws)
                            with open(f"{working_dir}/events_that_fit/{str(count)}.json", "w")  as f:
                                json.dump(event, f, indent=4)
                            count += 1
                            
                        elif tx["TransactionType"] == "Payment" and tx["Destination"] not in wallet_addrs:
                            print(f"Event Fits 1.2")
                            delivered_currency = event['meta']['delivered_amount']['currency']
                            delivered_issuer = event['meta']['delivered_amount']['issuer']
                            delivered_value = event['meta']['delivered_amount']['value']
                            try:
                                if delivered_currency in cc_list:
                                    for n in event['meta']['AffectedNodes']:
                                        if 'ModifiedNode' in n:
                                            if 'FinalFields' in n['ModifiedNode']:
                                                if 'Account' in n['ModifiedNode']['FinalFields'] and 'Balance' in n['ModifiedNode']['FinalFields']:
                                                    walllet_ad = n['ModifiedNode']['FinalFields']['Account']
                                    for c in wallets:
                                        if walllet_ad == c.classic_address:
                                            wallet = c
                                    await recieved_xrp(event, wallet)
                                    with open(f"{working_dir}/events_that_fit/{str(count)}.json", "w")  as f:
                                        json.dump(event, f, indent=4)
                                    count += 1
                            except Exception as e:
                                print(f"Event Fits 1.2 Error: {e}")
                                await write_error_to_file(event, f'Event Fits 1.2 Error: {e}')
                        else:
                            print(f"Event Dosnt Fit 1")
                            with open(f"{working_dir}/events_that_dont_fit/{str(count)}.json", "w")  as f:
                                json.dump(event, f, indent=4)
                            count += 1
                    else:
                        print(f"Event Dosnt Fit 2")
                        with open(f"{working_dir}/events_that_dont_fit_transaction/{str(count)}.json", "w")  as f:
                            json.dump(event, f, indent=4)
                        count += 1
                except Exception as e:
                    print(f"while True Error: {e}")
        except Exception as e:
            print(f'run Error: {e}')

async def create_tables():
    cm = f'''
    CREATE TABLE IF NOT EXISTS tk_masager (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        time BIGINT NOT NULL,
        action TEXT NOT NULL,
        err TEXT NOT NULL,
        message TEXT,
        xrp_amount NUMERIC,
        token_amount NUMERIC,
        token TEXT,
        token_cc TEXT,
        token_issuer TEXT,
        lp_token TEXT,
        lp_token_cc TEXT,
        lp_token_issuer TEXT,
        lp_amount NUMERIC
    );
    '''
    try:
        cursor.execute(cm)
        conn.commit()
        return 'success'
    except Exception as e:
        print('create_tables error:', e)
        return 'error'
    
if __name__ == '__main__':
    # PostgreSQL Connection Details
    if database:
        conn = psycopg2.connect(
            dbname = DB_NAME,
            user = DB_USER,
            password = DB_PASS,
            host = DB_HOST,
            port = DB_PORT
        )
        cursor = conn.cursor()
    working_dir = os.getcwd()
    print(f"Working Directory: {working_dir}")
    client = xrpl.clients.JsonRpcClient(JSON_RPC_URL)

    ###################### Set your wallet here ######################
    wallets = [Wallet.from_seed(CULT_OBEY_SEED)]
    wallet_addrs = [CULT_OBEY_ADDR]

    asyncio.run(run())
