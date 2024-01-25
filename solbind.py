import time
import threading

from solbind.settings import settings
from solbind.wallet import wallet
from solbind.menu import menu
from solbind.utils import utils

def main():

    logger = utils.logger()
    logger.print_and_log("Solbind is starting")

    if not settings.check_settings(logger):
        logger.print_and_log("Fix the settings issues before proceeding.")
        settings.configure_settings(logger)
        logger.print_and_log("Restart the program to confirm settings")
        time.sleep(5)
        exit(1)

    wallet.get_wallet_balances(settings.private_key, settings.rpc_url, logger)

    logger.print_and_log("Generating Threads")

    thread_exit = threading.Event()

    menu_thread = threading.Thread(target = menu.handle_menu, args = (thread_exit, logger ))

    menu_thread.start()

    menu_thread.join()

if __name__ == "__main__":
    main()
