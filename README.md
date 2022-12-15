# Ledger Asset DApps

This repository is a structured list of DApps descriptors cryptographycally signed by Ledger. Each blockchain has its own directory
(currently only Ethereum and some of its L2s are supported, but more will come). Inside an blockchain's directory, every DApp has its own directory as well and contains a file named `b2c.json` which is summary of the smart contracts and methods that Ledger supports. This file can refer to smart contract ABIs that are available in the `abis` folder. There is also a `*_signature.json` file, which is the signature of the DApp descriptor by Ledger.
The descriptors are send along with their signature to Ledger devices to verify their authenticity.

This repo can be seen as a way to add a supported dApp to Ledger's products. 
A product could parse this repository and use it to support new DApps. 
Currently, it is used by the Ethereum application and its plugins on Ledger Nano S/S+/X, to provide rich display when approving a DApp transaction.

# Signature

## Signature process
The signature takes into account the content of the `b2c.json` files and `abis` folder.

### Production signature
Only a quorum of Ledger employees is authorized to create new production signatures.

### Test signature
Not yet supported, coming soon.

# Contributing

If you want to contribute, please checkout the contributing guide [here](CONTRIBUTING.md).

# Tips
In case you need to update to lowercase all Ethereum addresses, you should be able to do this with something like
```
sed -e 's/\("0x.*"\)/\L\1/' b2c.json > b2c.json.new
```
