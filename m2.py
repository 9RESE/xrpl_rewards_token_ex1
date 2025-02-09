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
dotenv.load_dotenv()
import random

xrp_to_cold_wallet_percent = 0.02
xrp_threshold = 10000000
# cult lp 8EAB...15F
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
ccList = [cult_token['cc'], obey_token['cc']]
ccAmmList = [cult_token['amm_cc'], obey_token['amm_cc']]
rewards_from_wallet = 'rD56CsTcywRJqtcxJEyJ2QSSY7ZiBZJPzym'

TEST_JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
TEST_WS_URL = "wss://s.altnet.rippletest.net:51233" 
TEST_SEED = "sEdViCggFcoanFYa7XcoqXDKqMszySq"

JSON_RPC_URL = "https://s2.ripple.com:51234/"
WS_URL = "wss://s2.ripple.com:51233" 
JSON_RPC_URL = "https://s2.ripple.com:51234/"
NUM = os.getenv('MAIN_NUM')
CULT_OBEY_SEED = os.getenv('CULT_OBEY_SEED')
CULT_OBEY_ADDR = os.getenv('CULT_OBEY_ADDR')
COLD = os.getenv('COLD')
num_list = NUM.split()
error_count = 1

async def create_wallet_from_mnemonic_or_seed(mnemonic_or_seed):
    try:
        w1 = Wallet.from_seed(mnemonic_or_seed)
        return w1
    except Exception as e:
        print(f'create_wallet_from_mnemonic_or_seed error: {e}')

async def create_wallet():
    w1 = Wallet.create()
    print(w1)
    print(w1.seed)
    print(w1.public_key)
    print(w1.private_key)

    current_working_directory = os.getcwd()
    print('current_working_directory', current_working_directory)
    with open(f"{current_working_directory}/wallet.json", "w")  as f2:
        wallet_data = {
            'classic_address': {w1.classic_address},
            'seed': {w1.seed},
            'public_key': {w1.public_key},
            'private_key': {w1.private_key}
        }
        json.dump(wallet_data, f2, indent=4)
        f2.close()
        await set_trust_line(w1)
    return w1

async def set_trust_line(SEED):
    w1 = await create_wallet_from_mnemonic_or_seed(SEED)
    for c in tokens:
        try:
            trust_set = xrpl.models.transactions.TrustSet(
                account=w1.classic_address,
                limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                    currency=c['cc'],
                    issuer=c['token_issuer'],
                    value=c['max']
                )
            )
            await submit_and_wait(trust_set, w1)

            trust_set = xrpl.models.transactions.TrustSet(
                account=w1.classic_address,
                limit_amount=xrpl.models.amounts.IssuedCurrencyAmount(
                    currency=c['amm_cc'],
                    issuer=c['lp_issuer'],
                    value=c['amm_max']
                )
            )
            await submit_and_wait(trust_set, w1)
        except Exception as e:
            print(f'set_trust_line {c['token_issuer']} error: {e}')

    return w1

async def submit_and_wait(tx, w1):
    try:
        resp = xrpl.transaction.submit_and_wait(tx, client, w1)
        print(f"submit_and_wait resp: {resp}")
        return resp
    except Exception as e:
        err_msg = f'submit_and_wait error: {e}'
        print("submit_and_wait err", e)
        await write_error_to_file(tx, err_msg)
    return err_msg

async def write_error_to_file(event, err_msg):
    file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    if not os.path.exists(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/err/file_name"):
        os.makedirs(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/err/file_name")
    with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/err/{file_name}/{file_name}.json", "w")  as f:
                        json.dump(event, f, indent=4)
                        f.close()
    with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/err/{file_name}/{file_name}.txt", "w")  as f2:
                        f2.write(err_msg)
                        f2.close()

async def recieved_xrp(event, w1):
    print('Recieved XRP')
    try:
        xrp_in_wallet = get_balance(w1.classic_address, client)
        # xrp_in_wallet = 10000000
        # Send XRP to COLD
        if xrp_in_wallet > xrp_threshold:
            send_amount = xrp_in_wallet * xrp_to_cold_wallet_percent
            after_cold_deposit_amount = xrp_in_wallet - send_amount
            lp_deposit_amount = (xrp_in_wallet - after_cold_deposit_amount)/2 - 30
            try:
                payment_tx = Payment(
                    account=w1.classic_address,
                    destination=COLD,
                    amount=str(send_amount)
                )
                resp = await submit_and_wait(payment_tx)
                print(f'Sent XRP to COLD. resp = {resp}')
            except Exception as e:
                err_msg = f'Recieved XRP Send to COLD error {e}'
                print(err_msg)
                write_error_to_file(event, err_msg)

            try:
                for c in tokens:
                    amm_tx = AMMDeposit(
                        account=w1.classic_address,
                        asset={"currency": 'XRP'},
                        asset2={"currency": c['cc'], "issuer": c['token_issuer']},
                        amount=str(lp_deposit_amount),
                        amount2='0',
                        flags='tfSingleAsset'
                    )
                    resp2 = await submit_and_wait(amm_tx)
                    print(f"Deposited {lp_deposit_amount} Drops into {c['cc']} AMM pool. resp = {resp2}")
            except Exception as e:
                err_msg = f'Recieved XRP Send to AMM pool error {e}'
                print(err_msg)
                write_error_to_file(event, err_msg)
    except Exception as e:
        err_msg = f'Recieved XRP Send error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)


    # try:
    #     # TODO Check what was sold
    #     sold_currency_cc = ''
    #     sold_currency_amm_cc = ''
    #     sold_currency_issuer = ''
    #     amount = event['transaction']["Amount"]
    #     print(f"Received {amount} of XRP for the sale of {sold_currency_cc}")
    # except Exception as e:
    #     err_msg = f'Recieved XRP Check what was sold error {e}'
    #     print(err_msg)
    #     write_error_to_file(event, err_msg)

    # try:
    #     # Send XRP to COLD
    #     send_amount = int(amount * xrp_to_cold_wallet_percent)
    #     deposit_amount = amount - send_amount
        
    #     payment_tx = Payment(
    #         account=w1.classic_address,
    #         destination=COLD,
    #         amount=send_amount
    #     )
    #     resp = submit_and_wait(payment_tx)
    #     print(f'Sent XRP to COLD. resp = {resp}')
    # except Exception as e:
    #     err_msg = f'Recieved XRP Send to COLD error {e}'
    #     print(err_msg)
    #     write_error_to_file(event, err_msg)
    
    # try:
    #     # Deposit remaining XRP into AMM Pool
    #     amm_tx = AMMDeposit(
    #         account=w1.classic_address,
    #         asset={"currency": sold_currency_amm_cc, "issuer": sold_currency_issuer},
    #         amount=str(deposit_amount)
    #     )
    #     resp2 = submit_and_wait(amm_tx)
    #     print(f"Deposited {deposit_amount / 1_000_000} XRP into AMM pool. resp = {resp2}")
    # except Exception as e:
    #     err_msg = f'Recieved XRP Deposit remaining XRP into AMM Pool error {e}'
    #     print(err_msg)
    #     write_error_to_file(event, err_msg)

    # return 'testing'


async def recieved_lp(event, delivered_currency, delivered_issuer, delivered_value, w1):
    print(f"Received LP", delivered_currency, delivered_issuer, delivered_value)
    recieved_lp_amount = delivered_value
    recieved_lp_issuer = delivered_issuer 
    recieved_lp_cc = delivered_currency
    try:
        for c in tokens:
            if delivered_currency == c['amm_cc']:
                token_dict = c
        print(f"Received {recieved_lp_amount} of {recieved_lp_cc} LP Token ")
    except Exception as e:
        err_msg = f'Recieved LP Check what was sold error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)
    
    try:
        # Swap 50% of recieved_lp for token
        swap_amount = int(recieved_lp_amount * token_dict['lp_recieved_to_token_percent'])
        amm_withdraw = AMMWithdraw(
            account=w1.classic_address,
            asset = {"currency": token_dict['cc'], "issuer": token_dict['token_issuer']},
            asset2 = 'XRP',
            amount2 = None,
            lp_token_in = swap_amount,
        )
        resp = submit_and_wait(amm_withdraw)
        print(f"Swapped {swap_amount} LP1 for {token_dict['cc']}. resp = {resp}")
    except Exception as e:
        err_msg = f'Recieved LP Swap {token_dict['lp_recieved_to_token_percent']} of recieved_lp for token error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)

    # TODO ? Do set the token limit order here?

    try:
        # If LP1 balance > threshold, send 25% to COLD
        lp1_balance = get_balance(w1.classic_address, client, recieved_lp_cc)
        if lp1_balance > token_dict['amm_max']:
            send_lp1 = int(lp1_balance * 0.25)
            lp1_payment = Payment(
                account=w1.classic_address,
                destination=COLD,
                amount={"currency": recieved_lp_cc, "issuer": recieved_lp_issuer, "value": str(send_lp1)}
            )
            resp = submit_and_wait(lp1_payment)
            print(f"Sent {send_lp1} LP1 to COLD. resp = {resp}")
    except Exception as e:
        err_msg = f'Recieved LP Send 25% to COLD error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)

async def recieved_token(event, delivered_currency, delivered_issuer, delivered_value, w1):
    print(f"Received Tokens ", delivered_currency, delivered_issuer, delivered_value)
    recieved_currency_cc = delivered_currency
    recieved_currency_issuer = delivered_issuer
    recieved_amount = delivered_value
    try:
        for c in tokens:
            if delivered_currency == c['cc']:
                token_dict = c
    except Exception as e:
        err_msg = f'Recieved Token Check what was sold error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)
    
    # Make sell order for % above market
    try:
        offer_tx = OfferCreate(
            account=w1.classic_address,
            taker_pays={"currency": recieved_currency_cc, "issuer": recieved_currency_issuer, "value": str(recieved_amount)},
            taker_gets=str(int(recieved_amount * token_dict['token_sale_percent_above_market']))  # Selling at token_sale_percent_above_market% above market
        )
        rsp = submit_and_wait(offer_tx)
        print(f"Set sell order for {recieved_amount} T1 at {token_dict['token_sale_percent_above_market']}% over market price. resp = {rsp}")
    except Exception as e:
        err_msg = f'Recieved Token sell order for {token_dict['token_sale_percent_above_market']} above market error  {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)

async def limit_sale_xrp(event, sold_currency, sold_issuer):
    print('limit_sale_xrp')
    try:
        for c in tokens:
            if sold_currency == c['cc']:
                token_dict = c
        for n in event['meta']['AffectedNodes']:
            if 'ModifiedNode' in n:
                if 'FinalFields' in n['ModifiedNode']:
                    if 'Account' in n['ModifiedNode']['FinalFields'] and 'Balance' in n['ModifiedNode']['FinalFields']:
                        if n['ModifiedNode']['FinalFields']['Account'] == w1.classic_address:
                            final_xrp = int(n['ModifiedNode']['FinalFields']['Balance'])
                            prev_xrp = int(n['ModifiedNode']['PreviousFields']['Balance'])
                            recieved_xrp = final_xrp - prev_xrp
        print(f"Recieved {recieved_xrp} XRP ")
    except Exception as e:
        err_msg = f'Recieved LP Check what was sold error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)

    try:
        xrp_in_wallet = get_balance(w1.classic_address, client)
        # Send XRP to COLD
        if xrp_in_wallet > xrp_threshold:
            send_amount = int(recieved_xrp * xrp_to_cold_wallet_percent)
            cold_deposit_amount = recieved_xrp - send_amount
            lp_deposit_amount = (recieved_xrp - cold_deposit_amount)/2 - 30
            try:
                payment_tx = Payment(
                    account=w1.classic_address,
                    destination=COLD,
                    amount=str(send_amount)
                )
                resp = submit_and_wait(payment_tx)
                print(f'Sent XRP to COLD. resp = {resp}')
            except Exception as e:
                err_msg = f'Recieved XRP Send to COLD error {e}'
                print(err_msg)
                write_error_to_file(event, err_msg)

            try:
                for c in tokens:
                    amm_tx = AMMDeposit(
                        account=w1.classic_address,
                        asset={"currency": 'XRP'},
                        asset2={"currency": c['cc'], "issuer": c['token_issuer']},
                        amount=str(lp_deposit_amount),
                        amount2='0',
                        flags='tfSingleAsset'
                    )
                    resp2 = submit_and_wait(amm_tx)
                    print(f"Deposited {lp_deposit_amount} Drops into {sold_currency} AMM pool. resp = {resp2}")
            except Exception as e:
                err_msg = f'Recieved XRP Send to {sold_currency} AMM pool error {e}'
                print(err_msg)
                write_error_to_file(event, err_msg)
    except Exception as e:
        err_msg = f'Recieved XRP Send to COLD error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)
    
    try:
        # Deposit remaining XRP into AMM Pool
        amm_tx = AMMDeposit(
            account=w1.classic_address,
            asset={"currency": 'XRP'},
            asset2={"currency": sold_currency, "issuer": sold_issuer},
            amount=str(lp_deposit_amount),
            amount2='0',
            flags='tfSingleAsset'
        )
        resp2 = submit_and_wait(amm_tx)
        print(f"Deposited {lp_deposit_amount} Drops into {sold_currency} AMM pool. resp = {resp2}")
    except Exception as e:
        err_msg = f'Recieved XRP Deposit remaining XRP into AMM Pool error {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)

    return 'testing'


async def amm_withdrawl(event):
    print(f"AMMWithdraw")
    try:
        lp_in = event["transaction"]['LPTokenIn']['currency']
        for c in tokens:
            if lp_in == c['amm_cc']:
                token_dict = c
                recieved_lp_cc = token_dict['amm_cc']
                recieved_currency_cc = token_dict['cc']
                recieved_currency_issuer = token_dict['token_issuer'] # is this thee issuer?
                recieved_lp_issuer = token_dict['lp_issuer'] # is this thee issuer?
                recieved_lp_amount = int(event["transaction"]['LPTokenIn']["value"])
                recieved_lp_threshold = token_dict['amm_max']
        print(f"Withdrew {recieved_lp_amount} of {recieved_currency_cc} Token ")
    except Exception as e:
        err_msg = f'AMMWithdraw Check what was sold error  {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)
    
    # Make sell order for 4% above market
    try:
        offer_tx = OfferCreate(
            account=w1.classic_address,
            taker_pays={"currency": recieved_lp_cc, "issuer": recieved_lp_issuer, "value": str(int(recieved_lp_amount * token_dict['token_sale_percent_above_market']))},
            # taker_gets=str(int(recieved_amount * token_dict['token_sale_percent_above_market']))  # Selling at 4% above market
        )
        await submit_and_wait(offer_tx)
        # print(f"Set sell order for {recieved_amount} T1 at 4% over market price")
    except Exception as e:
        print(f'AMMWithdraw sell order for 4% above market error {e}')
        err_msg = f'AMMWithdraw sell order for 4% above market error  {e}'
        print(err_msg)
        write_error_to_file(event, err_msg)

# Handles incoming messages
async def handler(websocket):
    message = await websocket.recv()
    return message
# Use this to send API requests
async def api_request(options, websocket):
    try:
        await websocket.send(json.dumps(options))
        message = await websocket.recv()
        return json.loads(message)
    except Exception as e:
        return e

async def run():

    # Opens connection to ripple testnet
    count = 1
    async for ws in websockets.connect('wss://s2.ripple.com:51233'):
        try:
            subscribe_msg = {
                "command": "subscribe",
                "accounts": wallet_addr
            }
            await ws.send(json.dumps(subscribe_msg))
            print(f"Listening for transactions on {wallet_addr}")
            while True:
                try:
                    response = await ws.recv()
                    event = json.loads(response)
                    # print(f"Event: {event}")
                    if "transaction" in event:
                        tx = event["transaction"]
                        if tx["TransactionType"] == "Payment" and tx["Destination"] in wallet_addr:
                            print(f"Event Fits 1")
                            try:
                                delivered_currency = event['meta']['delivered_amount']['currency']
                                delivered_issuer = event['meta']['delivered_amount']['issuer']
                                delivered_value = event['meta']['delivered_amount']['value']
                                for c in wallets:
                                    if tx["Destination"] == c.classic_address:
                                        wallet = c
                                if delivered_currency in ccList:
                                    await recieved_token(event, delivered_currency, delivered_issuer, delivered_value, wallet)
                                elif delivered_currency in ccAmmList:
                                    await recieved_lp(event, delivered_currency, delivered_issuer, delivered_value, wallet)
                            except:
                                delivered_currency = 'xrp'
                                delivered_issuer = None
                                delivered_value = event['meta']['delivered_amount']
                                for c in wallets:
                                    if tx["Destination"] == c.classic_address:
                                        wallet = c
                                await recieved_xrp(event, wallet)
                            with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_fit/{str(count)}.json", "w")  as f:
                                json.dump(event, f, indent=4)
                            count += 1
                            
                        elif tx["TransactionType"] == "Payment" and tx["Destination"] not in wallet_addr:
                            print(f"Event Fits 1.2")
                            delivered_currency = event['meta']['delivered_amount']['currency']
                            delivered_issuer = event['meta']['delivered_amount']['issuer']
                            delivered_value = event['meta']['delivered_amount']['value']
                            try:
                                if delivered_currency in ccList:
                                    for n in event['meta']['AffectedNodes']:
                                        if 'ModifiedNode' in n:
                                            if 'FinalFields' in n['ModifiedNode']:
                                                if 'Account' in n['ModifiedNode']['FinalFields'] and 'Balance' in n['ModifiedNode']['FinalFields']:
                                                    walllet_ad = n['ModifiedNode']['FinalFields']['Account']
                                    for c in wallets:
                                        if walllet_ad == c.classic_address:
                                            wallet = c
                                    await recieved_xrp(event, wallet)
                            except:
                                print(f"Event Fits 1")
                            with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_fit/{str(count)}.json", "w")  as f:
                                json.dump(event, f, indent=4)
                            count += 1

                        # elif 'TakerGets' in event["transaction"] and 'currency' in event["transaction"]['TakerGets'] and event["transaction"]['TakerGets']['currency'] in ccList:
                        #     print(f"Event Fits 2")
                        #     await recieved_xrp(event)
                        #     with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_fit/{str(count)}.json", "w")  as f:
                        #         json.dump(event, f, indent=4)
                        #     count += 1
                        # elif 'SendMax' in event["transaction"] and 'currency' in event["transaction"]['SendMax'] and event["transaction"]['SendMax']['currency'] in ccList:
                        #     print(f"Event Fits 3")
                        #     await recieved_xrp(event)
                        #     with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_fit/{str(count)}.json", "w")  as f:
                        #         json.dump(event, f, indent=4)
                        #     count += 1
                        # elif 'LPTokenIn' in event["transaction"] and 'currency' in event["transaction"]['LPTokenIn'] and event["transaction"]['LPTokenIn']['currency'] in ccAmmList:
                        #     print(f"Event Fits 4")
                        #     await recieved_token(event)
                        #     with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_fit/{str(count)}.json", "w")  as f:
                        #         json.dump(event, f, indent=4)
                        #     count += 1
                        # elif 'Asset' in event["transaction"] and 'currency' in event["transaction"]['Asset'] and event["transaction"]['Asset']['currency'] in ccList and event["transaction"]['TransactionType'] == 'AMMDeposit':
                        #     print(f"Event Fits 5")
                        #     await recieved_lp(event)
                        #     with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_fit/{str(count)}.json", "w")  as f:
                        #         json.dump(event, f, indent=4)
                        #     count += 1
                        # elif 'Asset2' in event["transaction"] and 'currency' in event["transaction"]['Asset2'] and event["transaction"]['Asset2']['currency'] in ccList and event["transaction"]['TransactionType'] == 'AMMDeposit':
                        #     print(f"Event Fits 6")
                        #     await recieved_lp(event)
                        #     with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_fit/{str(count)}.json", "w")  as f:
                        #         json.dump(event, f, indent=4)
                        #     count += 1
                        else:
                            print(f"Event Dosnt Fit 1")
                            with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_dont_fit/{str(count)}.json", "w")  as f:
                                json.dump(event, f, indent=4)
                            count += 1
                    else:
                        print(f"Event Dosnt Fit 2")
                        with open(f"/home/rese/Documents/lp_massager/xrpl_rewards_token_ex1/events_that_dont_fit_transaction/{str(count)}.json", "w")  as f:
                            json.dump(event, f, indent=4)
                        count += 1
                except Exception as e:
                    print(f"while True Error: {e}")
        except Exception as e:
            print(f'run Error: {e}')

# Runs the webhook on a loop
def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
    print('Restarting Loop')
    # w1 = await create_wallet()
    # w1 = create_wallet_from_mnemonic_or_seed(TEST_SEED)
    # w1 = Wallet.from_secret_numbers(num_list)

if __name__ == '__main__':
    client = xrpl.clients.JsonRpcClient(JSON_RPC_URL)
    co_wallet = create_wallet_from_mnemonic_or_seed(CULT_OBEY_SEED)
    wallets = [co_wallet]
    wallet_addr = [CULT_OBEY_ADDR]
    main()



    # if "transaction" in event 
    #                 and if 'TakerGets' in event["transaction"]
    #                 and if 'currency' in event["transaction"]['TakerGets']
    #                 event["transaction"]['TakerGets']['currency'] in ccList 
                    