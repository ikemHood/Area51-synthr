from web3 import Web3  
node_url = "https://arbitrum-sepolia.blockpi.network/v1/rpc/public"

web3 = Web3(Web3.HTTPProvider(node_url)) 
print(web3.eth.gas_price)  