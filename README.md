XRPL Rewards Token Example 1
Looking to replicate the programmatic needs of the Cult/Obey tokenomics.

Open a terminal in the directory this file is in.
Set up a virtual enviroment
    python3 -m venv venv
    source venv/bin/activate
    .\venv\Scripts\activate
run 
    pip install requirements.txt

If you want to start with a new wallet 
Open the file makeWallet.py and set the name of the wallet you want, save, then run:
    python3 makeWallet.py

Now fund your wallet and edit the setTrust.py file with the new wallet and any new token parameters. You will have to look up the max and amm_max for the total amount the trust line can have.

Then run:
    python3 setTrust.py
If you want to import a Xaman set your numbers in the .env file

Also in the .env file you need to set your local directory this file is in and your cold wallet addr.

Now set up you massager.py script.
If you want to run a postgresql database for the bots action, setup your table and set the database veriables.

Set your:
    -xrp_to_cold_wallet_percent   This is the amount of XRP gains you want to send to the Col wallet

    -xrp_threshold     This is the amount of XRP you want to build up in the wallet befor you send some to the cold wallet and some into the amm pools


Set the token variables.
    -token_sale_percent_above_market   When you recieve a token they are sold emedietly. This is the percentage above the last market sale that you want to sale your token at. 

    -lp_recieved_to_token_percent    When you recieve lp tokens a percentage is single sided(token) withdrawn. This is the percentage of recieved tokens you want to withdraw.

    -amm_threshold        When your lp tokens reach a set ammount a percentage is sent to the cold wallet. This variable is for the amount of lp tokens the wallet holds when the movment of the lp tokens to the cold wallet is inishated.

    -amm_percent_to_cold    When your lp tokens reach a set ammount a percentage is sent to the cold wallet. This variable is for the percentage you want to move to the cold wallet.

If you want to add a token copy the cult_token as a template and change the variables. 
Then add the token dict to the 'tokens', 'cult_obey_cc_list', 'cult_obey_cc_amm_list', 'cc_list', and 'amm_list'
Update your trustlines if needed with the setTrust.py file.

If you added a new wallet add the seed and addr like they are for 'CULT_OBEY_SEED' and 'CULT_OBEY_ADDR.' Double check they are i the .env as well.
Add the wallet to the 'wallets' and 'wallet_addrs' at the bottom of the file.

One last thing to do change a file in the xrpl-py libary. In your editor open the lp_massager/xrpl/lib/python3.12/site-packages/xrpl/transaction/reliable_submission.py
change this bit of code:
    return asyncio.run(
        async_submit_and_wait(
            transaction,
            client,
            wallet,
            check_fee=check_fee,
            autofill=autofill,
            fail_hard=fail_hard,
        )
    )
to:
    return async_submit_and_wait(
            transaction,
            client,
            wallet,
            check_fee=check_fee,
            autofill=autofill,
            fail_hard=fail_hard,
        )

save your files.

now run the script in a terminal
    python3 ./massager.py
now fund your wallets with LP Tokens, Tokens, and XRP

