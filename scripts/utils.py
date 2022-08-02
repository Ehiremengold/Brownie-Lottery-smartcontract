from brownie import (
    config,
    accounts,
    network,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)
import pytest
from web3 import Web3


local_dev_env = ["development"]
forked_local_enviroment = ["mainnet-fork", "rinkeby"]


def get_account(id=None, index=None):
    # index given
    if index:
        return accounts[index]
    # id given
    if id:
        return accounts.load(id)
    # deploy locally
    if network.show_active() in local_dev_env:
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])


contracts_to_mock = {
    "eth_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}

# get_contract(contract_name) function takes in a string paramater
# i.e get_contract("eth_price_feed")
# contract_type i.e particular contract we are talking about
# contract_type = contracts_to_mock[contract_name="eth_price_feed"]
# check if we in a local_enviroment
# check if there has been a deployed mock
# False? deploy_mock()
# contract = contract_type[-1]
# True? not local network
# get contract_address from config
# contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)
# bcos we need to interact with this contract
# return contract
def get_contract(contract_name):
    """
    this fuction will grab the comtract addresses
    from the brownie config if defined, otherwise,
    it will deploy a mock version of that contract,
    and return that mock contract address

    Args:
        contract_name which will be a string, with
        key value pair to mock contracts.
        -
        returns the most recently deployed version of
        this contract
    """
    # not contract data-type, but the d contract 'type'
    contract_type = contracts_to_mock[contract_name]

    if network.show_active() in local_dev_env:
        # First if we are in a local block chain,
        # Second if no contract of that "type" has
        # been deployed.
        if len(contract_type) <= 0:
            deploy_mocks()
        # contract = last deployed version of the contract
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # interacting/getting a contract from its abi and address
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


# parameters needed to deploy the
# mockpricefeed(mockv3aggregator)
# see the mockv3 sol to clarify or github
DECIMALS = 8
# initial value=2000, 8 decimals 8 zeros
INITIAL_VALUE = 200000000000


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Mocks deployed!")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):
    # amount = 0.1 Link
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    # account is equal to passsed account
    # in the function if its given else use get_account()
    # option A of interacting/transfering token to a contract
    tx = link_token.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    # or
    # option B of interacting/transfering token to a contract
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    # tx.wait(1)
    print("Contract funded")
    return tx
