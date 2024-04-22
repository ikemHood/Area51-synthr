import random
from web3 import Web3

DEFAULT_GAS = 7000000 + random.randint(1, 100) # randomised to pass sybill detection
DEFAULT_GAS_PRICE = Web3.to_wei("0.4", "gwei")

# Tinker with this to get the right one based on demand in the network
LZ_VALUE = 0.00047
GENEREAL_SLEEP_TIMER = 1.5
