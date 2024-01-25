import os
import time

from solbind.wallet import wallet
from solbind.settings import settings

import matplotlib.pyplot as plt

class menu:

    def clear_screen():
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    @classmethod
    def handle_menu(cls, thread_exit, logger):
        term_size = os.get_terminal_size()
        tab = 0

        while not thread_exit.is_set():

            if tab == 0:
                menu.clear_screen()
                print(".▄▄ ·       ▄▄▌  ▄▄▄▄· ▪   ▐ ▄ ·▄▄▄▄  ".center(term_size.columns))
                print("▐█ ▀.  ▄█▀▄ ██•  ▐█ ▀█▪██ •█▌▐███▪ ██ ".center(term_size.columns))
                print("▄▀▀▀█▄▐█▌.▐▌██▪  ▐█▀▀█▄▐█·▐█▐▐▌▐█· ▐█▌".center(term_size.columns))
                print("▐█▄▪▐█▐█▌.▐▌▐█▌▐▌██▄▪▐█▐█▌██▐█▌██. ██ ".center(term_size.columns))
                print(" ▀▀▀▀  ▀█▄▀▪.▀▀▀ ·▀▀▀▀ ▀▀▀▀▀ █▪▀▀▀▀▀• ".center(term_size.columns))
                print("1.) Start    2.) Stop    3.) Refresh Wallet".center(term_size.columns))
                print("4.) View Logs    5.) View Market Stats    6.) Change Settings".center(term_size.columns))
                print("")
                wallet.print_wallet_balances()

                selection = input("")
                if selection == "1":
                    print("1")
                elif selection == "2":
                    thread_exit.set()
                elif selection == "3":
                    wallet.get_wallet_balances(settings.private_key, settings.rpc_url, logger)
                elif selection == "4":
                    tab = 1
                elif selection == "5":
                    tab = 2
                elif selection == "6":
                    settings.configure_settings(logger)

            elif tab == 1:
                menu.clear_screen()
                print(".▄▄ ·       ▄▄▌  ▄▄▄▄· ▪   ▐ ▄ ·▄▄▄▄  ".center(term_size.columns))
                print("▐█ ▀.  ▄█▀▄ ██•  ▐█ ▀█▪██ •█▌▐███▪ ██ ".center(term_size.columns))
                print("▄▀▀▀█▄▐█▌.▐▌██▪  ▐█▀▀█▄▐█·▐█▐▐▌▐█· ▐█▌".center(term_size.columns))
                print("▐█▄▪▐█▐█▌.▐▌▐█▌▐▌██▄▪▐█▐█▌██▐█▌██. ██ ".center(term_size.columns))
                print(" ▀▀▀▀  ▀█▄▀▪.▀▀▀ ·▀▀▀▀ ▀▀▀▀▀ █▪▀▀▀▀▀• ".center(term_size.columns))
                print("1.) Close".center(term_size.columns))
                print("")
                logger.read_log()

                selection = input("")
                if selection == "1":
                    tab = 0

            elif tab == 2:
                menu.clear_screen()
                print(".▄▄ ·       ▄▄▌  ▄▄▄▄· ▪   ▐ ▄ ·▄▄▄▄  ".center(term_size.columns))
                print("▐█ ▀.  ▄█▀▄ ██•  ▐█ ▀█▪██ •█▌▐███▪ ██ ".center(term_size.columns))
                print("▄▀▀▀█▄▐█▌.▐▌██▪  ▐█▀▀█▄▐█·▐█▐▐▌▐█· ▐█▌".center(term_size.columns))
                print("▐█▄▪▐█▐█▌.▐▌▐█▌▐▌██▄▪▐█▐█▌██▐█▌██. ██ ".center(term_size.columns))
                print(" ▀▀▀▀  ▀█▄▀▪.▀▀▀ ·▀▀▀▀ ▀▀▀▀▀ █▪▀▀▀▀▀• ".center(term_size.columns))
                print("1.) Close".center(term_size.columns))
                print("")

                stochastic_result = wallet.StochasticCalculator.process_json_and_calculate_stochastic(logger)

                # Check if the result is not None and if it has any rows
                if stochastic_result is not None and not stochastic_result.empty:
                    # Plot and save the chart
                    plt.figure(figsize=(15, 8))
                    plt.plot(stochastic_result['Timestamp'], stochastic_result['%K'], label='%K')
                    plt.plot(stochastic_result['Timestamp'], stochastic_result['%D'], label='%D')
                    plt.plot(stochastic_result['Timestamp'], stochastic_result['Smoothing'], label='Smoothing')
                    plt.title('Stochastic Oscillator Slow (14,3,3)')
                    plt.xlabel('Timestamp')
                    plt.ylabel('Percentage')
                    plt.legend()
                    plt.grid(True)
                    plt.savefig('stochastic_chart.png')
                    plt.show()
                else:
                    logger.print_and_log("Failed to fetch or process stochastic oscilator.")

                selection = input("")
                if selection == "1":
                    tab = 0

            time.sleep(0.25)
