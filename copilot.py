import xrpl
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import TrustSet, Payment
from xrpl.models.requests import Subscribe, Unsubscribe
from xrpl.transaction import send_reliable_submission
from xrpl.utils import xrp_to_drops

# Initialize client
client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")

# Create a new wallet W1
mnemonic = "your mnemonic here"
wallet_W1 = Wallet.from_mnemonic(mnemonic)

# Define cold wallet W2
wallet_W2_address = "rYourColdWalletAddressHere"

# Define token addresses
T1_address = "rYourTokenAddressHere"
LP1_address = "rYourLPTokenAddressHere"

# Set trust lines for W1
def set_trust_lines(wallet, token_address):
    trust_set = TrustSet(
        account=wallet.classic_address,
        limit_amount={
            "currency": token_address,
            "issuer": wallet.classic_address,
            "value": "10000000000"  # Set a high limit
        }
    )
    response = send_reliable_submission(trust_set, client)
    return response

set_trust_lines(wallet_W1, T1_address)
set_trust_lines(wallet_W1, LP1_address)

# Watch W1 for deposits
def on_transaction(tx):
    if tx["transaction"]["Destination"] == wallet_W1.classic_address:
        amount = int(tx["transaction"]["Amount"])
        if tx["transaction"]["TransactionType"] == "Payment":
            if tx["transaction"]["Amount"]["currency"] == "XRP":
                handle_xrp_deposit(amount)

def handle_xrp_deposit(amount):
    # Send 2% to W2
    fee = int(amount * 0.02)
    payment = Payment(
        account=wallet_W1.classic_address,
        destination=wallet_W2_address,
        amount=xrp_to_drops(fee)
    )
    send_reliable_submission(payment, client)
    
    # Deposit the rest into the AMM Pool
    deposit_amount = amount - fee
    # ...code to deposit into AMM Pool and receive LP1 tokens...

# Subscribe to transactions for W1
subscribe_request = Subscribe(
    accounts=[wallet_W1.classic_address]
)
client.request(subscribe_request)

# Unsubscribe when done
unsubscribe_request = Unsubscribe(
    accounts=[wallet_W1.classic_address]
)
client.request(unsubscribe_request)
