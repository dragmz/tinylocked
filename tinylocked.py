from dataclasses import dataclass
from datetime import datetime
from typing import Generator

from algosdk.v2client import algod
from tinylocker.utils.contracts import getTinylockerSignature, Environment

TINYLOCK_APP_ID = 445602322
TINYLOCK_ASA_ID = 410703201


@dataclass
class TinyLocked:
    address: str
    locker: str
    asset: int
    amount: int
    time: int

def tinylocked(ac: algod.AlgodClient, address: str) -> Generator[TinyLocked, None, None]:
    info = ac.account_info(address)

    assets = info.get("assets", [])
    for asset in assets:
        asset_id = asset["asset-id"]

        locker_address = getTinylockerSignature(ac, asset_id, TINYLOCK_APP_ID, TINYLOCK_ASA_ID, address,
                                                Environment.MainNet.value).address()
        locker_info = ac.account_info(locker_address)
        locker_assets = locker_info.get("assets", [])

        for locker_asset in locker_assets:
            locker_asset_id = locker_asset["asset-id"]

            if locker_asset_id == asset_id:
                amount = locker_asset["amount"]

                locker_local_state = locker_info['apps-local-state']
                lock_time = None

                for state in locker_local_state:
                    if state['id'] == TINYLOCK_APP_ID:
                        for kv in state['key-value']:
                            if kv['key'] == 'dGltZQ==':  # time
                                lock_time = kv['value']['uint']

                yield TinyLocked(
                    address=address,
                    locker=locker_address,
                    asset=locker_asset_id,
                    amount=amount,
                    time=lock_time)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='List assets locked on tinylock for given address')
    parser.add_argument('address', type=str, help='address to inspect')
    args = parser.parse_args()

    ac = algod.AlgodClient("", "https://algoexplorerapi.io", headers={'User-Agent': 'algosdk'})

    for item in tinylocked(ac, args.address):
        print("address", item.address, "has", item.amount, "of asset", item.asset, "locked at", item.locker, "until",
              datetime.fromtimestamp(item.time))
