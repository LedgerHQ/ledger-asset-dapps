
import json
import requests
import time
from pathlib import Path

COMPOUND_REPO_PATH = "external_ressources/compound-config/"
DAL_HOME_PATH = "../../"

ABI_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='
def get_etherscan_abi(contract_address):
    while True:
        time.sleep(0.3)

        # Get the ABI
        response = requests.get('%s%s'%(ABI_ENDPOINT, contract_address))
        response_json = response.json()

        #Failed! try again
        if (response_json['status'] == '0'):
            if (response_json['result'] == "Max rate limit reached, please use API Key for higher rate limit"):
                print("Failed to fetch " + str(contract_address) + " ABI. Retrying...")
                continue
            else:
                return None # Echec total!

        #Success! return abi
        abi_json = json.loads(response_json['result'])
        return abi_json



class ConfigFile:
    def __init__(self, cal_network_name, compound_contract_file, compound_abi_file):
        self.network_name = cal_network_name
        self.cal_abi_folder_path = Path(DAL_HOME_PATH) / cal_network_name / "compound" / "abis"
        if (self.cal_abi_folder_path.is_dir() == False):
            print("Creating folder " + str(self.cal_abi_folder_path))
            self.cal_abi_folder_path.mkdir(mode=0o775, parents=True, exist_ok=True)
        else:
            print("Found folder " + str(self.cal_abi_folder_path))

        self.contract_list_file = Path(DAL_HOME_PATH) / COMPOUND_REPO_PATH / 'networks' / Path(compound_contract_file)
        assert(self.contract_list_file.exists())

        self.abi_list_file = Path(DAL_HOME_PATH) / COMPOUND_REPO_PATH / 'networks' / Path(compound_abi_file)
        assert(self.abi_list_file.exists())


    def fill_abi_files(self):
        with self.contract_list_file.open() as contracts_fd, \
             self.abi_list_file.open() as abis_fd:
            contracts_json = json.load(contracts_fd)
            abis_json = json.load(abis_fd)

            failed_contracts = []

            # Get ABI for each contracts
            triplets = []
            for contract_name, contract_address in contracts_json["Contracts"].items():
                if (contract_name not in abis_json.keys()):
                    print("/!\\ Warning: " + contract_name + "(" + contract_address + ") ABI not found in listed compound repository. Fetching Etherscan ABI")
                    abi = get_etherscan_abi(contract_address)
                else:
                    print("ABI found in compound repository for " + contract_name + "(" + contract_address + ")")
                    abi = abis_json[contract_name]

                if (abi is not None):
                    triplets.append((contract_name, contract_address, abi))
                else:
                    print("Cannot find abi for contract " + contract_name + "(" + contract_address + ")" )
                    failed_contracts.append((contract_name, contract_address, abi))


            # Export ABI files
            for contract_name, contract_address, abi in triplets:
                cal_abi_file_path = (self.cal_abi_folder_path / contract_address.lower()).with_suffix(".abi.json")
                print("Writing " + str(cal_abi_file_path))
                with cal_abi_file_path.open(mode="w") as cal_abi_file_path_fd:
                    json.dump(abi, cal_abi_file_path_fd, indent=4, sort_keys=True)

            # Reporting
            total_count = len(triplets) + len(failed_contracts)
            print("===================================================================================================================")
            print("Network: " + str(self.network_name))
            print("Result {0}/{1} succeeded {2}/{1} failed.".format(len(triplets), total_count, len(failed_contracts)))
            for contract_name, contract_address, abi in failed_contracts:
                print ("Failed to get ABI for " + contract_name + "(" + contract_address + ")")
            print("===================================================================================================================")


networks = [ConfigFile(cal_network_name='ethereum', compound_contract_file='mainnet.json', compound_abi_file='mainnet-abi.json'),
            ConfigFile(cal_network_name='ethereum_goerli', compound_contract_file='goerli.json', compound_abi_file='goerli-abi.json'),
            ConfigFile(cal_network_name='ethereum_ropsten', compound_contract_file='ropsten.json', compound_abi_file='ropsten-abi.json')]

def main():
    for network in networks:
        network.fill_abi_files()

if __name__ == "__main__":
    main()
