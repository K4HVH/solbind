import base58
import base64
import json
import time
import requests
import os
import ccxt
import asyncio
import datetime
import pytz

import pandas as pd
import numpy as np

np.random.seed(42)

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders import message

from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TokenAccountOpts, TxOpts
from solana.rpc.commitment import Processed

from jupiter_python_sdk.jupiter import Jupiter, Jupiter_DCA


from solbind.settings import settings

class wallet:

    sol_balance = ["", "", ""]
    usdc_balance = ["", "", ""]

    coin_stats_json = []
    coin_stats_parsed = [0, 0, 0, 0]
    sol_data = []
    usdc_data = []

    @classmethod
    def retrieve_coin_stats(cls, logger):
        try:
            response = requests.get("https://min-api.cryptocompare.com/data/pricemultifull?fsyms=SOL,USDC&tsyms=AUD,USD")

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                cls.coin_stats_json = response.json()
                logger.print_and_log("Successfully retrieved coin stats")

                cls.coin_stats_parsed[0] = cls.coin_stats_json['RAW']['SOL']['AUD']['PRICE']
                cls.coin_stats_parsed[1] = cls.coin_stats_json['RAW']['SOL']['USD']['PRICE']
                cls.coin_stats_parsed[2] = cls.coin_stats_json['RAW']['USDC']['AUD']['PRICE']
                cls.coin_stats_parsed[3] = cls.coin_stats_json['RAW']['USDC']['USD']['PRICE']

                print(cls.coin_stats_parsed[1])
            else:
                # Print an error message if the request was not successful
                logger.print_and_log(f"Error while retrieving coin stats: {response.status_code} - {response.text}")
        except Exception as e:
            # Print an error message if an exception occurs
            logger.print_and_log(f"Exception while retrieving coin stats: {str(e)}")

    @classmethod
    def get_wallet_balances(cls, private_key, rpc_url, logger):
        # Connect to the Solana network
        client = Client(rpc_url)

        try:
            keypair = Keypair.from_bytes(base58.b58decode(private_key))
            pubkey = keypair.pubkey()

            # Get the balance of SOL
            cls.sol_balance[0] = client.get_balance(pubkey).value / (10 ** 9)

            # Find the USDC token account
            token_accounts_usdc = client.get_token_accounts_by_owner_json_parsed(pubkey, TokenAccountOpts(mint=Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"))).to_json()
            json_response = json.loads(token_accounts_usdc)
            cls.usdc_balance[0] = json_response["result"]["value"][0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]

            logger.print_and_log("Successfully retrieved wallet balances")
        except Exception as e:
            logger.print_and_log(f"Error while retrieving wallet balances: {e}")        # Edwards Point Error = Invalid key length
            time.sleep(5)                                                               # List Index Error = Key doesnt exist
            exit(1)

        cls.retrieve_coin_stats(logger)

        cls.sol_balance[1] = cls.sol_balance[0] * cls.coin_stats_parsed[0]
        cls.sol_balance[2] = cls.sol_balance[0] * cls.coin_stats_parsed[1]
        cls.usdc_balance[1] = cls.usdc_balance[0] * cls.coin_stats_parsed[2]
        cls.usdc_balance[2] = cls.usdc_balance[0] * cls.coin_stats_parsed[3]

    @classmethod
    def print_wallet_balances(cls):
        term_size = os.get_terminal_size()

        print(f"Wallet Balance: {cls.sol_balance[0]:.5f} SOL         ${cls.sol_balance[1]:.2f} AUD        ${cls.sol_balance[2]:.2f} USD".center(term_size.columns))
        print(f"Wallet Balance: {cls.usdc_balance[0]:.5f} USDC       ${cls.usdc_balance[1]:.2f} AUD       ${cls.usdc_balance[2]:.2f} USD".center(term_size.columns))
        print(f"Total Balance: ${cls.sol_balance[1] + cls.usdc_balance[1]:.2f} AUD       ${cls.sol_balance[2] + cls.usdc_balance[2]:.2f} USD".center(term_size.columns))
            
class Swap:
    def __init__(self, private_key_str, rpc_url):
        self.private_key = Keypair.from_bytes(base58.b58decode(private_key_str))
        self.rpc_url = rpc_url
        self.async_client = AsyncClient(rpc_url)
        self.jupiter = None  # Will be initialized when needed

    async def initialize_jupiter(self):
        if not self.jupiter:
            self.jupiter = Jupiter(self.async_client, self.private_key)

    async def swap(self, logger, input_mint, output_mint, amount, slippage_bps, retry_limit=3, for_output_amount=False):
        await self.initialize_jupiter()
        if for_output_amount:
            amount = round(self.calculate_required_input(output_mint, amount, logger))
        retry_count = 0
        while retry_count < retry_limit:
            try:
                transaction_data = await self.jupiter.swap(
                    input_mint=input_mint,
                    output_mint=output_mint,
                    amount=amount,
                    slippage_bps=slippage_bps
                )
                raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(transaction_data))
                signature = self.private_key.sign_message(message.to_bytes_versioned(raw_transaction.message))
                signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
                opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
                result = await self.async_client.send_raw_transaction(txn=bytes(signed_txn), opts=opts)
                transaction_id = json.loads(result.to_json())['result']
                print(f"Transaction successful: https://explorer.solana.com/tx/{transaction_id}")
                return transaction_id
            except Exception as e:
                retry_count += 1
                print(f"Attempt {retry_count} failed: {e}")
                if retry_count >= retry_limit:
                    print("Max retry limit reached. Transaction failed.")
                    break
                await asyncio.sleep(2)  # Wait before retrying

    def calculate_required_input(self, output_mint, desired_output_amount, logger):

        wallet.retrieve_coin_stats(logger)
        
        if output_mint == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":
            output_amount = (1 / wallet.coin_stats_parsed[1]) * desired_output_amount 
        elif output_mint == "So11111111111111111111111111111111111111112":
            output_amount = (wallet.coin_stats_parsed[1] / 1) * desired_output_amount 
    
        return output_amount

    async def close(self):
        await self.async_client.close()

class Trader:
    
    @staticmethod
    def wait_until_end_of_trading_period(trading_period, trader_exit=None):
        # Get current date and time in GMT
        gmt = pytz.timezone('GMT')
        current_datetime_gmt = datetime.datetime.now(gmt)

        # Calculate the start of the current trading period
        start_of_trading_period = current_datetime_gmt.replace(hour=0, minute=0, second=0, microsecond=0)
        while start_of_trading_period + trading_period < current_datetime_gmt:
            start_of_trading_period += trading_period

        # Calculate the end of the current trading period
        end_of_trading_period = start_of_trading_period + trading_period

        # Print information
        print(f"Current time (GMT): {current_datetime_gmt}")
        print(f"Start of trading period (GMT): {start_of_trading_period}")
        print(f"End of trading period (GMT): {end_of_trading_period}")

        # Calculate the duration to wait until the end of the current trading period
        time_to_wait = (end_of_trading_period - current_datetime_gmt).total_seconds()

        # Print information about the wait
        print(f"Waiting until end of trading period... ({datetime.timedelta(seconds=time_to_wait)})")

        # Wait until end of trading period or exit flag is set
        check_interval = 1  # Check every second
        while time_to_wait > 0:
            if trader_exit is not None and trader_exit.is_set():
                print("Exit flag set. Exiting early...")
                return
            sleep_duration = min(time_to_wait, check_interval)
            time.sleep(sleep_duration)
            time_to_wait -= sleep_duration

        print("End of trading period reached!")
        
    @staticmethod
    def run_trader(trader_exit, logger):
        while not trader_exit.is_set():
            Trader.wait_until_end_of_trading_period(datetime.timedelta(minutes=1), trader_exit)

            if not trader_exit.is_set():  # Make sure we arent going to trade on shutdown
                trade_instance = Swap(settings.private_key, settings.rpc_url)

                asyncio.run(trade_instance.swap(
                    logger, 
                    input_mint="So11111111111111111111111111111111111111112",
                    output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    amount=int(1 * 1000000000),
                    slippage_bps=1,
                    retry_limit=3, 
                    for_output_amount=True
                ))
        return