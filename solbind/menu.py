import os
import time
import asyncio
import threading

from solbind.wallet import *
from solbind.settings import settings

import matplotlib.pyplot as plt

class menu:

    def clear_screen():
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def solbind_logo(term_size):
        print(".▄▄ ·       ▄▄▌  ▄▄▄▄· ▪   ▐ ▄ ·▄▄▄▄  ".center(term_size.columns))
        print("▐█ ▀.  ▄█▀▄ ██•  ▐█ ▀█▪██ •█▌▐███▪ ██ ".center(term_size.columns))
        print("▄▀▀▀█▄▐█▌.▐▌██▪  ▐█▀▀█▄▐█·▐█▐▐▌▐█· ▐█▌".center(term_size.columns))
        print("▐█▄▪▐█▐█▌.▐▌▐█▌▐▌██▄▪▐█▐█▌██▐█▌██. ██ ".center(term_size.columns))
        print(" ▀▀▀▀  ▀█▄▀▪.▀▀▀ ·▀▀▀▀ ▀▀▀▀▀ █▪▀▀▀▀▀• ".center(term_size.columns))

    @classmethod
    def handle_menu(cls, thread_exit, logger):
        term_size = os.get_terminal_size()
        tab = 0

        while not thread_exit.is_set():

            if tab == 0:
                menu.clear_screen()
                menu.solbind_logo(term_size)
                print("1.) Start    2.) Exit    3.) Refresh Wallet".center(term_size.columns))
                print("4.) View Logs    5.) View Market Stats    6.) Change Settings".center(term_size.columns))
                print("")
                wallet.print_wallet_balances()

                selection = input("")
                if selection == "1":
                    tab = 1
                elif selection == "2":
                    thread_exit.set()
                elif selection == "3":
                    wallet.get_wallet_balances(settings.private_key, settings.rpc_url, logger)
                elif selection == "4":
                    tab = 4
                elif selection == "5":
                    tab = 5
                elif selection == "6":
                    settings.configure_settings(logger)

            elif tab == 1:
                menu.clear_screen()
                menu.solbind_logo(term_size)
                print("1.) Stop".center(term_size.columns))
                print("")

                trader_exit = threading.Event()
                
                trader_thread = threading.Thread(target = Trader.run_trader, args = (trader_exit, logger ))

                trader_thread.start()

                selection = input("")
                if selection == "1":
                    trader_exit.set()
                    tab = 0        

            elif tab == 4:
                menu.clear_screen()
                menu.solbind_logo(term_size)
                print("1.) Close".center(term_size.columns))
                print("")
                logger.read_log()

                selection = input("")
                if selection == "1":
                    tab = 0

            elif tab == 5:
                menu.clear_screen()
                menu.solbind_logo(term_size)
                print("1.) Close".center(term_size.columns))
                print("")
                
                # trade_instance = Trade(settings.private_key, settings.rpc_url)
                # asyncio.run(trade_instance.swap(
                #     input_mint="So11111111111111111111111111111111111111112",
                #     output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                #     amount=int(1 * 1000000000),
                #     slippage_bps=1
                # ))

                # asyncio.run(trade_instance.swap(
                #     input_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                #     output_mint="So11111111111111111111111111111111111111112",
                #     amount=int(1 * 1000000),
                #     slippage_bps=1
                # ))

                selection = input("")
                if selection == "1":
                    tab = 0

            time.sleep(0.25)
