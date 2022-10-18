# Contributing to Ledger Asset DApps

Thank you for adding your DApp and decreasing the amount of blind signing in this world.

If you wish to add/update contracts or 712 messages for a DApp, create a PR targeting ``main`` with your changes.

712 messages need to validate against this schema https://github.com/LedgerHQ/ledger-asset-dapps/blob/main/ethereum/eip712.schema.json

Please run `python scripts/validate_files.py --debug` before you commit, this will validate and also format the files correctly.
