Ubuntu Server for script and postgresql nft tracking and distributions databases.
XRPL Transaction Server(optional)
Things to be carfull of
    Seed phrases- Those who have acess to the computer the script will be running will have access to the seed phrase of the wallet used to hold/send rewards. There are ways to mitagate this depending on if we use the cloud or a local computer.

Build the NFT/Wallet Database
Build script that
    gets nft id and wallet entries from db
    iterate through the db results
        check result wallet xrpl current holdings for all nfts in db results
            remove entries in db results that fit the wallet/nft pairing
        if a db results entry has that wallet/nft pair after removing all exsisting nfts search for the transaction that sent it to a different wallet and update the database nft entry to reflect the new wallet.
    get all uniqe wallets in db
    iterate through unique wallets
        get all entries for that wallet from the db
        get quanities of different NFTS
        get lp positions
        calculate rewards
        send rewards
        update distributions db
    




-UGA NFTs - Grant $UGA
? Ratio of UGA NFTs to $UGA
? Distribution Frequency 

-$UGA LP Providers - Grant $REDACTED
? Ratio of (% $UGA LP Held) to $REDACTED
? Distribution Frequency 


-Elder/ Council./ SOG NFTs - Grant $REDACTED
? Elder Ratio of NFTs to $REDACTED
? Council Ratio of NFTs to $REDACTED
? SOG Ratio of NFTs to $REDACTED
? Distribution Frequency 


-$REDACTED LP Providers - Grant $UGA LP Tokens
? Ratio of (% $REDACTED LP Held) to $UGA LP Tokens
? Distribution Frequency















Open a terminal in the directory this file is in.
Set up a virtual enviroment
    python3 -m venv venv
    source venv/bin/activate
    .\venv\Scripts\activate
run 
    pip install requirements.txt

