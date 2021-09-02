"""
Vote with test transaction on goerli.
"""
import os
import time
from typing import Tuple

from brownie import accounts, network

from utils.voting import create_vote
from utils.evm_script import (
    encode_call_script,
    decode_evm_script,
    calls_info_pretty_print
)
from utils.config_goerli import (
    lido_dao_finance_address,
    lido_dao_voting_address,
    lido_dao_token_manager_address
)
from utils.config import (
    prompt_bool, get_deployer_account
)
from utils.finance import encode_eth_transfer

try:
    from brownie import interface

except ImportError:
    print(
        'You\'re probably running inside Brownie console. '
        'Please call:\n'
        'set_console_globals(interface=interface)'
    )


def set_console_globals(**kwargs):
    """Import interfaces from Brownie environment."""
    global interface
    interface = kwargs['interface']


def make_fund_test_call_script(
        target_address: str,
        eth_in_wei: int, finance: interface.Finance  # noqa
) -> Tuple[str, str]:
    """Create encoded transaction from Lido Finance address to target."""
    return encode_eth_transfer(
        recipient=target_address,
        amount=eth_in_wei,
        reference=f'Test payout: '
                  f'from Lido Finance protocol '
                  f'to {target_address}.',
        finance=finance
    )


def as_wei(eth_amount: float) -> int:
    """Convert ethereum to wei"""
    factor = 10 ** 18
    return round(eth_amount * factor)


def start_vote(tx_params, silent=False):
    # Lido contracts:
    finance = interface.Finance(lido_dao_finance_address)
    voting = interface.Voting(lido_dao_voting_address)
    token_manager = interface.TokenManager(
        lido_dao_token_manager_address
    )

    # Current vote specific addresses and constants:
    target_address = '0xc4AB398EFE38800Aab46493C31845377Bd6b9bc6'
    test_tx_eth_amount = as_wei(1)  # 1 ETH as wei

    # Calls encoding:
    encoded_calls = encode_call_script([
        # Encoded test transaction
        make_fund_test_call_script(
            target_address, test_tx_eth_amount, finance
        )
    ])

    human_readable_calls = decode_evm_script(
        encoded_calls, verbose=False, specific_net='goerli'
    )

    if not silent:
        for ind, call in enumerate(
                human_readable_calls
        ):
            print(f'Script #{ind + 1}.')
            print(calls_info_pretty_print(call))
            print('---------------------------')
        print()

        print('Does it look good?')
        resume = prompt_bool()
        while resume is None:
            resume = prompt_bool()
        if not resume:
            return -1, None

    return create_vote(
        voting=voting,
        token_manager=token_manager,
        vote_desc=(
            f'Omnibus vote: '
            f'1) Create test transaction '
            f'from Lido finance to target address: '
            f'{target_address}'
        ),
        evm_script=encoded_calls,
        tx_params=tx_params
    )


def main():
    # deployer = accounts.at(
    #     os.getenv(
    #         'DEPLOYER',
    #         '0xc4AB398EFE38800Aab46493C31845377Bd6b9bc6'
    #     ),
    #     force=True
    # )
    deployer = get_deployer_account()
    print(f'Deployer: {deployer.address}.')
    print(f'Active network: {network.show_active()}')
    vote_id, _ = start_vote({
        'from': deployer,
        'gas_price': '200 gwei'
    })
    print(f'Vote created: {vote_id}')

    time.sleep(5)
