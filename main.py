import random
import logging
import time
from web3 import Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
import os

from utils.actions import build_and_send_transaction, read_function_from_contract
from utils.utils import read_abi
from utils.constants import LZ_VALUE, GENEREAL_SLEEP_TIMER
from dotenv import load_dotenv

load_dotenv()

ACTION_MULTIPLIER = int(os.getenv('ACTION_MULTIPLIER', 5))

account_address = os.getenv('WALLET_ADDRESS')
private_key = os.getenv('WALLET_PRIVATE_KEY')
url = os.getenv('RPC_URL')

web3 = Web3(Web3.HTTPProvider(url))
web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

if __name__ == "__main__":
    # Check wallet balance in ETH
    main_contract_address = "0xe0875CBD144Fe66C015a95E5B2d2C15c3b612179"
    faucet_address = "0xfb2c2196831DeEb8311d2CB4B646B94Ed5eCF684"
    bridge_contract = "0x2F1673beD3E85219E2B01BC988ABCc482261c38c"
    eth_usd_chainlink_feed = "0xd30e2101a97dcbAeBCBC04F14C3f624E67A35165"
    main_abi = read_abi(f"./abis/{main_contract_address}.json")
    chainlink_abi = read_abi(f"./abis/{eth_usd_chainlink_feed}.json")
    bridge_abi = read_abi(f"./abis/{bridge_contract}.json")

    running_total_diff = 0
    amount_to_swap = 10
    for c in range(ACTION_MULTIPLIER):
        try:
            initial_balance = web3.from_wei(
                web3.eth.get_balance(account_address), "ether"
            )
            logging.info(f"Wallet balance: {initial_balance} ETH")

            # Faucet action preparation
            synthr_faucet_token_amount = int(
                10 * 1e18 + random.randint(0, 100) * 1e18
            )  # Faucet amount to extract

            # Synthr Faucet extract tokens
            abi = read_abi(f"./abis/{faucet_address}.json")
            build_and_send_transaction(
                web3_client=web3,
                contract_address=Web3.to_checksum_address(faucet_address),
                function_name="faucetToken",
                abi=abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(synthr_faucet_token_amount,),
            )
            time.sleep(GENEREAL_SLEEP_TIMER)

            # Approve Synthr faucet tokens
            build_and_send_transaction(
                web3_client=web3,
                contract_address=faucet_address,
                function_name="approve",
                abi=abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(
                    main_contract_address,
                    115792089237316195423570985008687907853269984665640564039457584007913129639935,
                ),
            )
            time.sleep(GENEREAL_SLEEP_TIMER)

            # Deposit Synthr faucet tokens
            build_and_send_transaction(
                web3_client=web3,
                contract_address=main_contract_address,
                function_name="issueSynths",
                abi=main_abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(
                    "0x4545544800000000000000000000000000000000000000000000000000000000",
                    synthr_faucet_token_amount,
                    0,
                    "0x4c617965725a65726f0000000000000000000000000000000000000000000000",
                    0,
                    False,
                ),
            )
            time.sleep(GENEREAL_SLEEP_TIMER)

            # Issue sUSD
            issue_amount = int(1e18 * 10_000) + random.randint(
                0, int(1e8)
            )  # 10,000 sUSD + random amount

            build_and_send_transaction(
                web3_client=web3,
                contract_address=main_contract_address,
                function_name="issueSynths",
                abi=main_abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    0,
                    issue_amount,
                    "0x4c617965725a65726f0000000000000000000000000000000000000000000000",
                    0,
                    False,
                ),
            )
            time.sleep(GENEREAL_SLEEP_TIMER)

            # Burn sUSD
            build_and_send_transaction(
                web3_client=web3,
                contract_address=main_contract_address,
                function_name="burnSynths",
                abi=main_abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(
                    int(issue_amount // 1e8),
                    "0x7355534400000000000000000000000000000000000000000000000000000000",
                    "0x4c617965725a65726f0000000000000000000000000000000000000000000000",
                ),
            )
            time.sleep(GENEREAL_SLEEP_TIMER)

            # Withdraw Collateral
            build_and_send_transaction(
                web3_client=web3,
                contract_address=main_contract_address,
                function_name="withdrawCollateral",
                abi=main_abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(
                    "0x4545544800000000000000000000000000000000000000000000000000000000",
                    int(
                        issue_amount // 1e8
                    ),  # Feel free to change it to any amount you want,
                    # if you want to test liquidation functionality of the protocol.
                    "0x4c617965725a65726f0000000000000000000000000000000000000000000000",
                    0,
                    False,
                ),
            )
            time.sleep(GENEREAL_SLEEP_TIMER)

            # Cross chain swap, you need lz_value (to add more fees), to change chainID,
            random_swap_ammount = random.randint(
                int(30 * 1e18), int(100 * 1e18))  # randomized between 30 to 100
            min_amount_percentage = 0.9996822  # slippage
            # why u no know maths anon?
            min_amount = int(random_swap_ammount * (1 - min_amount_percentage))
            build_and_send_transaction(
                web3_client=web3,
                contract_address=main_contract_address,
                function_name="exchangeAtomically",
                abi=main_abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(
                    "0x7355534400000000000000000000000000000000000000000000000000000000",  # sourceCurrencyKey
                    random_swap_ammount,  # sourceAmount
                    # destinationCurrencyKey
                    "0x7345544800000000000000000000000000000000000000000000000000000000",
                    min_amount,  # minAmount
                    "0x4c617965725a65726f0000000000000000000000000000000000000000000000",  # bridgeName
                    10106,  # destChainId
                    False,  # erc20Payment
                ),
                lz_value=LZ_VALUE,
            )
            time.sleep(GENEREAL_SLEEP_TIMER)

            # Same chain swap
            eth_usd_price_raw = read_function_from_contract(
                web3_client=web3,
                contract_address=eth_usd_chainlink_feed,
                function_name="latestAnswer",
                abi=chainlink_abi,
            ).call()
            eth_usd_price = (
                int(eth_usd_price_raw) / 1e8 if eth_usd_price_raw != 0 else 0
            )
            usd_eth_price = 0.003 / eth_usd_price
            # Calculate the minimum amount in sUSD
            min_amount_susd = int(0.97 * amount_to_swap * usd_eth_price * 1e18)
            # Assuming 3% slippage
            build_and_send_transaction(
                web3_client=web3,
                contract_address=main_contract_address,
                function_name="exchangeAtomically",
                abi=main_abi,
                account_address=account_address,
                private_key=private_key,
                function_args=(
                    "0x7355534400000000000000000000000000000000000000000000000000000000",  # sourceCurrencyKey
                    int(amount_to_swap * 1e18),  # sourceAmount
                    # destinationCurrencyKey
                    "0x7345544800000000000000000000000000000000000000000000000000000000",
                    min_amount_susd,  # minAmount in sUSD
                    "0x4c617965725a65726f0000000000000000000000000000000000000000000000",  # bridgeName
                    0,  # destChainId
                    False,  # erc20Payment
                ),
            )

            # Bridge only every % 10 == 0 iteration
            if c % 10 == 0:
                # Bridge some sUSD to another chain, similar to cross chain swap,
                # you need to test via UI to get the right arguments.
                bridge_amount = int(10 * 1e18) + random.randint(0, 10000000000)
                build_and_send_transaction(
                    web3_client=web3,
                    contract_address=bridge_contract,
                    function_name="bridgeSynth",
                    abi=bridge_abi,
                    account_address=account_address,
                    private_key=private_key,
                    function_args=(
                        account_address,
                        "0x7355534400000000000000000000000000000000000000000000000000000000",
                        bridge_amount,
                        "0x4c617965725a65726f0000000000000000000000000000000000000000000000",
                        10106,
                        False,
                    ),
                    lz_value=LZ_VALUE,
                )
                time.sleep(GENEREAL_SLEEP_TIMER)

            balance = web3.from_wei(
                web3.eth.get_balance(account_address), "ether")
            diff = initial_balance - balance
            running_total_diff += diff
            logging.warning(
                f"Difference from initial balance: {-diff} ETH, from {initial_balance} to {balance}"
            )
            logging.warning(
                f"Running total difference: {-running_total_diff} ETH")
            # If no exception occurs, log the success message
            logging.info("Actions completed successfully")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            logging.info("Retrying the failed actions...")
            continue  # Continue to the next iteration of the loop

        time.sleep(GENEREAL_SLEEP_TIMER)
