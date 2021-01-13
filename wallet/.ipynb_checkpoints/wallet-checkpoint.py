import subprocess
import json
import os
from dotenv import load_dotenv
from constants import *
from bit import wif_to_key
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from bit.network import NetworkAPI
from pathlib import Path
from getpass import getpass
from bit import PrivateKeyTestnet
from web3.gas_strategies.time_based import medium_gas_price_strategy

load_dotenv()

mnemonic = os.getenv("MNEMONIC")

# Defining a function to derive path, address, private key and public key for each coin.  Coin symbol ("BTC"/"ETH", etc) are fed into the function.

def derive_wallets(coin):
    command = f'php derive -g --mnemonic="{mnemonic}" --cols=path,address,privkey,pubkey --coin={coin} --numderive=3 --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    keys = json.loads(output)
    print(keys)
    return (keys)

# Creating a dictionary to store data from derive_wallets function for ETH & BTCTEST.  ETH & BTCTEST were previoulsy defined in constants.py file. 

coins = {
    ETH: derive_wallets(ETH),
    BTCTEST: derive_wallets(BTCTEST)
}
# coins = [derive_wallets(ETH), derive_wallets(BTCTEST)]

print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

# Code below used to navigate through dictionaries and print private keys. Code below references first account address of: 0x54116383D6FEAe0284BD79B71509Ca8B74B5071a.

print(coins[ETH][0]["privkey"])
print(coins[BTCTEST][0]["privkey"])

# Defining a function to convert private_key strings to an account object for bit/web3 to transact on.

def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    else:
        return PrivateKeyTestnet(priv_key)
    
# Printing to test function on each coin.

print(priv_key_to_account(ETH, coins[ETH][0]["privkey"]))    
print(priv_key_to_account(BTCTEST, coins[BTCTEST][0]["privkey"])) 

# Creating variables to pass into each function that will already be in the needed format. 

eth_account = priv_key_to_account(ETH, coins[ETH][0]["privkey"])
btc_account = priv_key_to_account(BTCTEST, coins[BTCTEST][0]["privkey"])

# w3 variables set to allow usage in create_tx function

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

# Function created to generate a raw, unsigned transaction that contains all metadata needed to transact.  

def create_tx(coin, account, recipient, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas(
            {"from": eth_account.address, "to": recipient, "value": amount}
        )
        return {
            "from": eth_account.address,
            "to": recipient,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(eth_account.address),
            "chainID": w3.eth.chainId
    }
    
    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(btc_account.address, [(recipient, amount, BTC)])
    
# Testing to ensure transaction can be created - NOTE: Need to have local server open to work.  Ganache was opened up to allow function to run properly and have local server to access for ETH. 

create_tx(ETH, eth_account, '0x65b2F9eEc1b964E6CDb793E4ba4Ff19eAeF4CF0c', 1)

# Testing with address from prior PoA blockchain. 
create_tx(ETH, eth_account, '0x89320751b21A5c56158F03224d8A6037586D3aFA', 1)

create_tx(BTCTEST, btc_account, 'mwQDPPDTxWWz3aYupQVdSyGpswVPn9JHYV', .000001)

# Creating a function to send created transactions.  Calls create_tx function previously created.

def send_tx(coin, account, recipient, amount):
    raw_tx = create_tx(coin, account, recipient, amount)
    signed_tx = account.sign_transaction(raw_tx)
    if coin == ETH:
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(result.hex())
        return result.hex()
    if coin == BTCTEST:
        print(signed_tx)
        return NetworkAPI.broadcast_tx_testnet(signed_tx)

# Testing to ensure send_tx function works properly. Numerous transactions tested. Example of two transaction hashes below. 

# ETH Transaction 1: 0x526a2acfb1ad870ec69660e7abaf128e34edcbfb066693350e778709a4445991
# ETH Transaction 2: 0xcf3c1fed59f9589985940e8d685c0b28cff25c0273bacfd1125f423a21b5f97a
# BTCTEST Transaction: d32acdc22a745444e69f1e6cd8e12c27ae9f9ba98e3092f3f1d7d1e010b4a6e2

send_tx(ETH, eth_account, '0x65b2F9eEc1b964E6CDb793E4ba4Ff19eAeF4CF0c', 1)

# Testing after adding account to prior PoA blockchain.
send_tx(ETH, eth_account, '0x89320751b21A5c56158F03224d8A6037586D3aFA', 1)

send_tx(BTCTEST, btc_account, 'mt3p3zCExoVCWrHziCqWn3RT5PubQRwCco', .000001)
    
    
# Sent a transaction to BTCTEST address below, via testnet faucet.

# Transaction sent
# TxID: d8a0e0f8908db7e2c8ce79f1e0852681ba6cccf5409b845b6c9148ce298e3a76
# Address: mwQDPPDTxWWz3aYupQVdSyGpswVPn9JHYV
# Amount: 0.001


