XRPL Rewards Token Example 1
Looking to replicate the programmatic needs of the Cult/Obey tokenomics.





Ok I want to develop a python script that will "massage" a AMM Pool. Here is the concept:
The bot wallet: The script should allow for the creation of a new wallet using the mnemonic or number sets secret options. We will call this wallet W1. 

The cold wallet: The script should take an xrpl wallet address and call it W2.

The wallets hold XRP, the a token we will call T1, and the T1 AMM LP token we will call LP1. The script should take the T1 and LP1 address's and set the trust lines on W1 for them.

The script should watch W1 with a websocket for the deposit of XRP, T1 or LP1. 

If W1 receives XRP it should send 2% of the XRP to the W2 wallet and the rest should be deposited into the TI AMM Pool in exchange for LP1 tokens. 

If W1 receives XRP it should send 2% of the XRP to the W2 wallet and the rest should be deposited into the TI AMM Pool in exchange for LP1 tokens. 


cult lp -> token -> Limit Order
obey token -> Limit Order
Limit Order -> XRP -> x% xrp cold wallet -> xrp to LP -> (lp > x -> cold wallet) -> lp to token -> Limit Order


test_wallet
seed=sEdViCggFcoanFYa7XcoqXDKqMszySq
public_key=ED8B47A2863A9466C8CF840F48067B81B846148333DD178C9ABF33C109EBF9CC82
private_key=ED3CC7D359B79CC31B116FCA3AFACBE33749F2C29C147F1A01AFF82AF340C19772