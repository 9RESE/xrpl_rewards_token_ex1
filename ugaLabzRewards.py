from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.models.requests import AccountNFTs, NFTInfo, AMMInfo, AccountLines
from xrpl.models import AMMInfo
from xrpl.wallet import Wallet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.transaction import sign_and_submit

import os
from datetime import datetime, timedelta
import psycopg2
import csv
import asyncio
import dotenv
dotenv.load_dotenv()

JSON_RPC_URL = "https://s2.ripple.com:51234/"
WS_URL = "wss://s2.ripple.com:51233" 

DB_NAME = "uganomics"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

nft_issuer = 'rJzn2G1VoBFynqy9A8iRTJnbSt2bf6PPb9'
max_gnosis_daily_rewards_for_uga_lp_contributers = 2904.66 # GNOSIS Rewards 2,904.66 $GNOSIS per day for UGA LP Token Holders By Percentage
max_uga_lp_daily_rewards_for_gnosis_lp_contributers = 5479.44 # Uga LP Rewards 5479.44 Uga LP per day for GNOSIS LP Token Holders By Percentage
max_nft_gnosis_rewards = 1930.07 # NFT Rewards 1930.07 $GNOSIS per day for NFT Holders
sog_holder_rewards_rate = 7.68 # SOG 7.68 $GNOSIS per day per SOG Nft
consular_holder_rewards_rate = 3.59 # Consular 3.59 $GNOSIS per day per Consular Nft
elder_holder_rewards_rate = .52 # Elder .52 $GNOSIS per day per Elder Nft

uga_token = {
    'token_name': 'uga',
    'token_issuer': 'rBFJGmWj6YaabVCxfsjiCM8pfYXs8xFdeC',
    'cc': 'UGA',
    'lp_name': 'cult_lp',
    'lp_issuer': 'r36ARnypS7x9gTJxohQQpBgG7QF9Ti5cXL',
    'amm_cc': '038F8F9444CA41839DFA137696EC1E0F77F4DD1E'
}

gnosis_token = {
    'token_name': 'gnosis',
    'token_issuer': 'rHUQ3xYC2hwfJa9idjjmsCcb5hP3qZiiTM',
    'cc': '474E4F5349530000000000000000000000000000',
    'lp_name': 'gnosis_lp',
    'lp_issuer': 'rLCzs77qasvWGRDQdqNbd9dhPQHgeF22ca',
    'amm_cc': '0307E6A9765465FC45E544FF3FD664EE583C4AB4'
}

token_list = [uga_token, gnosis_token]

async def create_tables():
    cm = f'''
    CREATE TABLE IF NOT EXISTS nfts(
        nft_id TEXT PRIMARY KEY NOT NULL,
        nft_name TEXT NOT NULL,
        current_account TEXT NOT NULL,
        collection TEXT NOT NULL,
        image TEXT NOT NULL,
        ipfs_json TEXT NOT NULL,
        last_updated timestamp NOT NULL
    );
    '''
    cursor.execute(cm)

    cm = f'''
    CREATE TABLE IF NOT EXISTS lp_pools(
        id SERIAL PRIMARY KEY NOT NULL,
        account TEXT NOT NULL,
        pool TEXT NOT NULL,
        percentage NUMERIC NOT NULL,
        total_tokens NUMERIC NOT NULL,
        pool_token_count NUMERIC NOT NULL,
        date timestamp NOT NULL
    );
    '''
    cursor.execute(cm)

    cm = f'''
    CREATE TABLE IF NOT EXISTS rewards_distributions(
        id SERIAL PRIMARY KEY NOT NULL,
        wallet TEXT NOT NULL,
        uga_token NUMERIC NOT NULL,
        uga_lp_token NUMERIC NOT NULL,
        gnosis_token NUMERIC NOT NULL,
        gnosis_lp_token NUMERIC NOT NULL,
        brothren_nfts NUMERIC,
        counsoler_nfts NUMERIC ,
        sog_nfts NUMERIC,
        elder_nfts NUMERIC,
        distributed boolean NOT NULL,
        tx_hash TEXT,
        date timestamp NOT NULL
    );
    '''
    cursor.execute(cm)

    cm = f'''
    CREATE TABLE IF NOT EXISTS errors(
        id SERIAL PRIMARY KEY NOT NULL,
        wallet_being_processed TEXT,
        error_msg TEXT NOT NULL,
        date timestamp NOT NULL
    );
    '''
    cursor.execute(cm)

    conn.commit()
    try:
        cursor.execute(cm)
        conn.commit()
        return 'success'
    except Exception as e:
        err_msg = f'create_tables Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def construct_nfts_db():
    all_nft_ids = []
    with open(f'/home/rese/Documents/rese/UGA/airdrops/uga_airdrops/alluga.csv', 'r') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            nft_id = row['\ufeff"NFT_ID"']
            print('nft_id:', nft_id)
            nft_name = row['Name']
            print('nft_name:', nft_name)
            owner = row['Owner']
            if row['Taxon'] == '369':
                collection = 'Consular'
            elif row['Taxon'] == '9':
                collection = 'Gnostic Elder'
            elif row['Taxon'] == '776':
                collection = 'SOG'
            elif row['Taxon'] == '333':
                collection = 'UGA Brothren'
            print('collection:', collection)
            image = row['Image']
            print('image:', image)
            ipfs_json = row['URI']
            print('ipfs_json:', ipfs_json)
            try:
                q = "INSERT INTO nfts (nft_id, nft_name, current_account, collection, image, ipfs_json, last_updated) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(q, (nft_id, nft_name, owner, collection, image, ipfs_json, datetime.now()))
            except Exception as e:
                print('Insert Error:', e)
    conn.commit()               
        # nft_id TEXT PRIMARY KEY NOT NULL,
        # nft_name TEXT NOT NULL,
        # current_account TEXT NOT NULL,
        # collection TEXT NOT NULL,
        # image TEXT NOT NULL,
        # ipfs_json TEXT NOT NULL,
        # last_updated timestamp NOT NULL    

async def get_unique_current_wallets_from_nfts():
    try:
        query = "SELECT DISTINCT current_account FROM nfts"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        err_msg = f'get_unique_current_wallets_from_nfts Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def get_all_nft_ids():
    try:
        query = "SELECT nft_id FROM nfts"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        err_msg = f'get_all_nft_ids Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def get_all_nft_ids_of_wallet_in_db(wallet):
    try:
        query = "SELECT nft_id FROM nfts WHERE current_account = %s"
        cursor.execute(query, (wallet,))
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        err_msg = f'get_all_nft_ids_of_wallet_in_db Error:{e}'
        print(err_msg)
        await error(err_msg, wallet)
        return 'err'

async def get_nft_collection_count_of_wallet_in_db(account, collection):
    try:
        query = "SELECT COUNT(*) FROM nfts WHERE current_account = %s AND collection = %s"
        cursor.execute(query, (account, collection,))
        rows = cursor.fetchall()
        return [row for row in rows]
    except Exception as e:
        err_msg = f'get_nft_collection_count_of_wallet_in_db Error:{e}'
        print(err_msg)
        await error(err_msg, account)
        return 'err'

async def update_lp_trust_lines(lp_addr, lp_cc, pool):
    try:
        addr_with_trust_lines = []
        amm_request = AccountLines(
            ledger_index="validated",
            account=lp_addr
        )
        resp = await client.request(amm_request)
        amm_rep = resp.result['lines']
        for line in amm_rep:
            if line['balance'] != 0 and line['balance'] != 0.0 and line['balance'] != '0.0' and line['currency'] == lp_cc:
                addr_with_trust_lines.append({
                    'account': line['account'],
                    'balance': abs(float(line['balance']))
                })
        
        if pool == 'uga':
            uga_total_lp_token_count = await get_lp_total_token_count(uga_token['lp_issuer'])
            for ulpw in addr_with_trust_lines:
                percentage = ulpw['balance'] / float(uga_total_lp_token_count)
                q = "INSERT INTO lp_pools (account, pool, percentage, total_tokens, pool_token_count, date) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(q, (ulpw['account'], 'uga', percentage, ulpw['balance'], uga_total_lp_token_count, datetime.now()))
            conn.commit()
        else:
            gnosis_total_lp_token_count = await get_lp_total_token_count(gnosis_token['lp_issuer'])
            for glpw in addr_with_trust_lines:
                percentage = glpw['balance'] / float(gnosis_total_lp_token_count)
                q = "INSERT INTO lp_pools (account, pool, percentage, total_tokens, pool_token_count, date) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(q, (glpw['account'], 'gnosis', percentage, glpw['balance'], gnosis_total_lp_token_count, datetime.now()))
            conn.commit()
    except Exception as e:
        err_msg = f'update_lp_trust_lines Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def get_lp_total_token_count(lp_addr):
    try:
        response = await client.request(AMMInfo(amm_account=lp_addr))
        return response.result['amm']['lp_token']['value']
    except Exception as e:
        err_msg = f'get_lp_total_token_count Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def update_nft_wallet(nft_id, wallet):
    try:
        q = "UPDATE nfts SET current_account = %s WHERE nft_id = %s"
        cursor.execute(q, (wallet, nft_id))
        conn.commit()
    except Exception as e:
        err_msg = f'update_nft_wallet Error:{e}'
        print(err_msg)
        await error(err_msg, wallet)
        return 'err'

async def update_nft_owners():
    print('update_nft_owners')
    try:
        # Get all unique walets in nfts db
        unique_wallets_in_db = await get_unique_current_wallets_from_nfts()
        # for each wallet, get all nft ids in db
        for wallet in unique_wallets_in_db[:1]:
            current_nft_ids_in_wallet_in_db = await get_all_nft_ids_of_wallet_in_db(wallet)
            
            # check wallet has all previous_nft_ids and has no new ones
            req = AccountNFTs(account=wallet)
            wallet_ledger_nfts = await client.request(req)

            ledger_nft_ids = []
            missing_nft_ids = []
            new_nft_ids = []
            if 'account_nfts' in wallet_ledger_nfts.result:
                for nft in wallet_ledger_nfts.result['account_nfts']:
                    if nft['Issuer'] == nft_issuer:
                        ledger_nft_ids.append(nft['NFTokenID'])
                
            if len(ledger_nft_ids) == 0: 
                for nft_id in ledger_nft_ids:
                    if nft_id not in current_nft_ids_in_wallet_in_db:
                        new_nft_ids.append(nft_id)
                    else:
                        new_nft_ids.append(nft_id)
                        print('nft_id in current_nft_ids_in_wallet_in_db:', nft_id)

            if missing_nft_ids == [] and new_nft_ids != []:
                for nft_id in new_nft_ids:
                    await update_nft_wallet(nft_id, wallet)

            elif missing_nft_ids != [] and new_nft_ids == []:
                for nft_id in missing_nft_ids:
                    nft_info = NFTInfo(nft_id)
                    response = await client.request(nft_info)
                    new_wallet = response.result['owner']
                    await update_nft_wallet(nft_id, new_wallet)  

            elif missing_nft_ids != [] and new_nft_ids != []:
                for nft_id in new_nft_ids:
                    await update_nft_wallet(nft_id, wallet)
                for nft_id in missing_nft_ids:
                    nft_info = NFTInfo(nft_id)
                    response = await client.request(nft_info)
                    new_wallet = response.result['owner']
                    await update_nft_wallet(nft_id, new_wallet)

            elif ledger_nft_ids == []:
                for nft_id in current_nft_ids_in_wallet_in_db:
                    nft_info = NFTInfo(nft_id)
                    response = await client.request(nft_info)
                    new_wallet = response.result['owner']
                    await update_nft_wallet(nft_id, new_wallet) 
    except Exception as e:
        err_msg = f'update_nft_owners Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def calculate_nft_rewards():
    print('calculate_nft_rewards')
    try:
        nft_wallets = await get_unique_current_wallets_from_nfts()
        total_all_wallets_nft_rewards_gnosis_rewards = 0
        for wallet in nft_wallets:
            wallet_nft_gnosis_rewards = 0
            resp = await get_nft_collection_count_of_wallet_in_db(wallet, 'UGA Brothren')
            brothren_count = resp[0][0]

            resp = await get_nft_collection_count_of_wallet_in_db(wallet, 'SOG')
            sog_count = resp[0][0]
            wallet_nft_gnosis_rewards += sog_count * sog_holder_rewards_rate

            resp = await get_nft_collection_count_of_wallet_in_db(wallet, 'Consular')
            consular_count = resp[0][0]
            wallet_nft_gnosis_rewards += consular_count * consular_holder_rewards_rate

            resp = await get_nft_collection_count_of_wallet_in_db(wallet, 'Gnostic Elder')
            elder_count = resp[0][0]
            wallet_nft_gnosis_rewards += elder_count * elder_holder_rewards_rate

            total_all_wallets_nft_rewards_gnosis_rewards += wallet_nft_gnosis_rewards

            q = "INSERT INTO rewards_distributions (wallet, uga_token, uga_lp_token, gnosis_token, gnosis_lp_token, brothren_nfts, counsoler_nfts, sog_nfts, elder_nfts, distributed, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(q, (wallet, 0, 0, wallet_nft_gnosis_rewards, 0, brothren_count, consular_count, sog_count, elder_count, False, datetime.now()))
        conn.commit()
        return total_all_wallets_nft_rewards_gnosis_rewards
    except Exception as e:
        err_msg = f'calculate_nft_rewards Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'
           
async def calculate_lp_contributer_rewards(pool):
    try:
        print('calculate_lp_contributer_rewards pool:', pool)
        two_hours_ago = datetime.now() - timedelta(hours=2)
        q = """SELECT account, percentage, total_tokens FROM lp_pools WHERE date >= %s AND pool = %s"""
        cursor.execute(q, (two_hours_ago, pool))
        lp_wallets_db = cursor.fetchall()
        total_all_wallets_lp_contributer_rewards = 0
        for w in lp_wallets_db:
            if w[1] == 0.0:
                continue
            else:
                if pool == 'uga':
                    wallet_lp_holder_rewards = float(w[1]) * max_gnosis_daily_rewards_for_uga_lp_contributers
                else:
                    wallet_lp_holder_rewards = float(w[1]) * max_uga_lp_daily_rewards_for_gnosis_lp_contributers
                total_all_wallets_lp_contributer_rewards += wallet_lp_holder_rewards
                q = "INSERT INTO rewards_distributions (wallet, uga_token, uga_lp_token, gnosis_token, gnosis_lp_token, distributed, date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                if pool == 'uga':
                    cursor.execute(q, (w[0], 0, 0, wallet_lp_holder_rewards, 0, False, datetime.now()))
                else:
                    cursor.execute(q, (w[0], 0, wallet_lp_holder_rewards, 0, 0, False, datetime.now()))
        conn.commit()
        return total_all_wallets_lp_contributer_rewards
    except Exception as e:
        err_msg = f'calculate_lp_contributer_rewards Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def get_most_recent_rewards_distribution():
    try:
        print('get_most_recent_rewards_distribution:')
        query = "SELECT date FROM rewards_distributions WHERE distributed = TRUE ORDER BY date DESC LIMIT 1"
        cursor.execute(query)
        row = cursor.fetchone()
        return row
    except Exception as e:
        err_msg = f'get_most_recent_rewards_distribution Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'

async def pay_rewards(to_wallet_addr, reward_amount, currency):
    print('pay_rewards')
    if currency == 'gnosis':
        issued_c = IssuedCurrencyAmount(
            currency=gnosis_token['cc'],
            issuer=gnosis_token['token_issuer'],
            value=reward_amount
        )
        w = Wallet.from_seed(os.getenv('gnosis_rewards_wallet_seed'))
        db_column = 'gnosis_token'
    elif currency == 'gnosis_lp':
        issued_c = IssuedCurrencyAmount(
            currency=gnosis_token['amm_cc'],
            issuer=gnosis_token['lp_issuer'],
            value=reward_amount
        )
        w = Wallet.from_seed(os.getenv('gnosis_lp_rewards_wallet_seed'))
        db_column = 'gnosis_lp_token'
    elif currency == 'uga_lp':
        issued_c = IssuedCurrencyAmount(
            currency=uga_token['amm_cc'],
            issuer=uga_token['lp_issuer'],
            value=reward_amount
        )
        w = Wallet.from_seed(os.getenv('uga_lp_rewards_wallet_seed'))
        db_column = 'uga_lp_token'
    try:
        p = Payment(account=w, amount=issued_c, destination=to_wallet_addr, destination_tag=1)
        payment_resp = await sign_and_submit(p, client, w)
        print('payment_resp:', payment_resp)
        if payment_resp['engine_result'] == 'tesSUCCESS':
            payment_tx_hash = payment_resp['transaction']['hash']
            print('payment_resp:', payment_resp['transaction']['hash'])
            q = "UPDATE rewards_distributions SET distributed = TRUE, tx_hash = %s WHERE wallet = %s AND distributed = FALSE AND %s != 0"
            cursor.execute(q, (payment_tx_hash, to_wallet_addr, db_column))
            conn.commit()
        else:
            err_msg = f'Payment Failed:{payment_resp}'
            print(err_msg)
            error(err_msg, to_wallet_addr)
    except Exception as e:
        err_msg = f'pay_rewards Error:{e}'
        print(err_msg)
        await error(err_msg, to_wallet_addr)

async def error(error_msg, wallet):
    q = "INSERT INTO errors (wallet_being_processed, error_msg, date) VALUES (%s, %s, %s)"
    cursor.execute(q, (wallet, error_msg, datetime.now()))
    conn.commit()

async def process_rewards():
    print('Process Rewards')
    try:
        last_sucssesful_rewards_distribution_date = await get_most_recent_rewards_distribution()
        if last_sucssesful_rewards_distribution_date == None:
            last_sucssesful_rewards_distribution_date = datetime.now() - timedelta(hours=24)
        q = "SELECT date FROM rewards_distributions ORDER BY date DESC LIMIT 1"
        cursor.execute(q)
        last_rewards_date = cursor.fetchone()
        if last_rewards_date == None or last_rewards_date[0] < datetime.now() - timedelta(hours=23):
            await update_nft_owners()
            total_all_wallets_nft_rewards_gnosis_rewards = await calculate_nft_rewards()

            await update_lp_trust_lines(uga_token['lp_issuer'], uga_token['amm_cc'], 'uga')
            await update_lp_trust_lines(gnosis_token['lp_issuer'], gnosis_token['amm_cc'], 'gnosis')
            total_all_wallets_daily_gnosis_rewards_for_uga_lp_contributers = await calculate_lp_contributer_rewards('uga')
            total_all_wallets_daily_uga_lp_rewards_for_gnosis_lp_contributers = await calculate_lp_contributer_rewards('gnosis')
            
            try:
                if abs(max_nft_gnosis_rewards - total_all_wallets_nft_rewards_gnosis_rewards) <= 303.70000000000437 and abs(max_uga_lp_daily_rewards_for_gnosis_lp_contributers - total_all_wallets_daily_uga_lp_rewards_for_gnosis_lp_contributers) <= 0.5 and abs(max_gnosis_daily_rewards_for_uga_lp_contributers - total_all_wallets_daily_gnosis_rewards_for_uga_lp_contributers) <= 0.5:
                    print('Rewards are within 0.5 of the daily rewards')
                    q = "SELECT DISTINCT wallet FROM rewards_distributions WHERE distributed = FALSE"
                    cursor.execute(q)
                    wallets = cursor.fetchall()
                    for wallet in wallets:
                        q = "SELECT * FROM rewards_distributions WHERE wallet = %s AND distributed = FALSE"
                        cursor.execute(q, (wallet[0],))
                        rewards = cursor.fetchall()
                        print('rewards:', type(rewards))
                        uga_lp_rewards = 0
                        gnosis_rewards = 0
                        for reward in rewards:
                            uga_lp_rewards += reward[3]
                            gnosis_rewards += reward[4]
                        if uga_lp_rewards != 0:
                            await pay_rewards(wallet[0], uga_lp_rewards, 'uga_lp')
                        if gnosis_rewards != 0:
                            await pay_rewards(wallet[0], gnosis_rewards, 'gnosis')
                else:
                    err_msg = 'Rewards totals are not within 0.5 of the daily rewards'
                    print(err_msg)
                    await error(err_msg, '') 
            except Exception as e:
                err_msg = f'process_rewards Rewards Checker and payer Error:{e}'
                print(err_msg)
                await error(err_msg, '')
                return 'err'
    except Exception as e:
        err_msg = f'process_rewards Error:{e}'
        print(err_msg)
        await error(err_msg, '')
        return 'err'       

async def run():
    # delete the lp_pool table
    q = "DELETE FROM lp_pools"
    cursor.execute(q)
    q = "DELETE FROM rewards_distributions"
    cursor.execute(q)
    conn.commit()
    await create_tables()
    # await construct_nfts_db()
    await process_rewards()
    
# Main execution
if __name__ == '__main__':
    conn = psycopg2.connect(
        dbname = DB_NAME,
        user = DB_USER,
        password = DB_PASS,
        host = DB_HOST,
        port = DB_PORT
    )
    cursor = conn.cursor()
    client = JsonRpcClient(JSON_RPC_URL)
    asyncio.run(run())
