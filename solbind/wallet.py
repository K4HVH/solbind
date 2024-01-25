import base58
import json
import time
import requests
import os

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from solbind.settings import settings

from solders.keypair import Keypair
from solders.pubkey import Pubkey

from solana.rpc.api import Client
from solana.rpc.types import TokenAccountOpts

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


    class StochasticCalculator:
        @staticmethod
        def parse_json_response(api_response, logger):
            # Check if the response is successful
            if api_response.get('Response') == 'Success':
                data = api_response.get('Data', {}).get('Data', [])

                parsed_data = []
                for entry in data:
                    time = entry.get('time')
                    high = entry.get('high')
                    low = entry.get('low')
                    open_price = entry.get('open')
                    volume_from = entry.get('volumefrom')
                    volume_to = entry.get('volumeto')
                    close = entry.get('close')

                    parsed_data.append({
                        'time': time,
                        'high': high,
                        'low': low,
                        'open': open_price,
                        'volume_from': volume_from,
                        'volume_to': volume_to,
                        'close': close
                    })

                return parsed_data
            else:
                logger.print_and_log("Historic API response was not successful.")
                return None

        @staticmethod
        def calculate_slow_stochastic(high, low, close, timestamp):
            k_period = 14
            d_period = 3
            smoothing_period = 3

            data = pd.DataFrame({'High': high, 'Low': low, 'Close': close, 'Timestamp': timestamp})
            
            # Calculate %K
            data['Lowest Low'] = data['Low'].rolling(window=k_period, min_periods=1).min()
            data['Highest High'] = data['High'].rolling(window=k_period, min_periods=1).max()
            data['%K'] = ((data['Close'] - data['Lowest Low']) / (data['Highest High'] - data['Lowest Low'])) * 100
            
            # Calculate %D (3-period SMA of %K)
            data['%D'] = data['%K'].rolling(window=d_period, min_periods=1).mean()
            
            # Calculate Smoothing (3-period SMA of %D)
            data['Smoothing'] = data['%D'].rolling(window=smoothing_period, min_periods=1).mean()

            # Drop unnecessary columns
            data = data.drop(['Lowest Low', 'Highest High'], axis=1)
            
            return data[['Timestamp', '%K', '%D', 'Smoothing']].dropna()

        @classmethod
        def process_json_and_calculate_stochastic(cls, logger):
            # Parse JSON response
            response = requests.get("https://min-api.cryptocompare.com/data/v2/histohour?fsym=SOL&tsym=USD&limit=336")
            parsed_data = cls.parse_json_response(response.json(), logger)

            if parsed_data:
                # Extract required data for Slow Stochastic Oscillator calculation
                high_data = [entry['high'] for entry in parsed_data]
                low_data = [entry['low'] for entry in parsed_data]
                close_data = [entry['close'] for entry in parsed_data]
                timestamp_data = [entry['time'] for entry in parsed_data]

                # Calculate Slow Stochastic Oscillator
                stochastic_result = cls.calculate_slow_stochastic(high_data, low_data, close_data, timestamp_data)

                # Print the latest values of %K, %D, and Smoothing
                latest_values = stochastic_result.iloc[-1]
                latest_k = latest_values['%K']
                latest_d = latest_values['%D']
                latest_smoothing = latest_values['Smoothing']

                logger.print_and_log(f"Latest Values: K={latest_k:.2f}%, D={latest_d:.2f}%, Smooth={latest_smoothing:.2f}%")

                return stochastic_result
            else:
                return None