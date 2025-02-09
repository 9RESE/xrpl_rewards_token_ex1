from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.models import TrustSet, Payment, AMMDeposit
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.ledger import get_account_info, get_trust_lines
from xrpl.utils import drops_to_xrp
import asyncio

# Function to create wallet from mnemonic or seed (number set secret)
def create_wallet_from_mnemonic_or_seed(mnemonic_or_seed):
    return Wallet.from_seed(mnemonic_or_seed)

W1 = create_wallet_from_mnemonic_or_seed("your_mnemonic_or_seed")
W2_address = "rYourColdWalletAddress"  # Cold wallet address

# Connect to the XRP Ledger
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")  # Use Testnet for testing

def set_trust_line(wallet, currency, issuer):
    trust_set = TrustSet(
        account=wallet.address,
        limit_amount=IssuedCurrencyAmount(
            currency=currency,
            issuer=issuer,
            value="1000000"  # Set a high limit, adjust as needed
        )
    )
    return submit_and_wait(trust_set, client, wallet)

# Assuming T1 and LP1 details
T1_currency = "T1"
T1_issuer = "rT1IssuerAddress"
LP1_currency = "LP1"
LP1_issuer = "rLP1IssuerAddress"

set_trust_line(W1, T1_currency, T1_issuer)
set_trust_line(W1, LP1_currency, LP1_issuer)

async def watch_for_deposits(wallet, callback):
    async with client as client:
        await client.subscribe_account(wallet.address)
        while True:
            updates = await client.account_tx(wallet.address)
            for tx in updates.result['transactions']:
                if tx['tx']['TransactionType'] == 'Payment':
                    callback(tx['tx']['Amount'], tx['tx']['Account'])
            await asyncio.sleep(10)  # Check every 10 seconds

async def handle_deposit(amount, sender):
    if isinstance(amount, str):  # XRP payment
        xrp_amount = drops_to_xrp(amount)
        transfer_amount = xrp_amount * 0.02  # 2% to W2
        deposit_amount = xrp_amount - transfer_amount

        # Send 2% to W2
        payment = Payment(
            account=W1.address,
            destination=W2_address,
            amount=str(int(transfer_amount * 1e6))  # Convert back to drops
        )
        submit_and_wait(payment, client, W1)

        # Deposit the rest to AMM
        amm_deposit = AMMDeposit(
            account=W1.address,
            asset=IssuedCurrencyAmount(currency=T1_currency, issuer=T1_issuer),
            asset2="XRP",  # Assuming XRP is the other asset in the pool
            amount=deposit_amount
        )
        submit_and_wait(amm_deposit, client, W1)
    else:
        print("Non-XRP token deposit detected, not handled yet.")

# Start monitoring
asyncio.run(watch_for_deposits(W1, handle_deposit))