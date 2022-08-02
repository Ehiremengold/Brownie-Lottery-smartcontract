from multiprocessing.dummy import active_children

from yaml import emit
from brownie import exceptions, network, Lottery, accounts, config
from web3 import Web3
from scripts.deploy_lottery import deploy_lottery, enter_lottery
from scripts.utils import get_contract, local_dev_env, get_account, fund_with_link
import pytest

NETWORK_ENVIROMENT = [
    "rinkeby" "mainnet-fork",
]

# testing the entrance fee with $50 and above
# $50 to eth is 0.025 with the rate defined below
def test_get_entrance_fee():
    # if we are not in development, skip tests
    if network.show_active() not in local_dev_env:
        pytest.skip()
    # arrange
    # act
    # assert
    lottery = deploy_lottery()
    # 2000 usd/eth
    # 50 ? xeth
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()
    assert entrance_fee == expected_entrance_fee


# test that the lottery has to be started before entering.
def test_cant_enter_unless_started():
    if network.show_active() not in local_dev_env:
        pytest.skip()

    lottery = deploy_lottery()
    # when we try to enter a lottery that has not started/OPENED,
    # it will revert an error, the pytest.raises catches such errors
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enterLottery({"from": get_account(), "value": lottery.getEntranceFee()})


# now test if they can enter, when its opened
def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in local_dev_env:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    # Act
    lottery.startLottery({"from": account})
    lottery.enterLottery({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    # the user that started and entered the lottery
    # is equal to the first user in the array
    assert lottery.players(0) == account


# test if lottery can end
def test_can_end_lottery():
    # Arrange
    if network.show_active() not in local_dev_env:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()

    # start lottery
    lottery.startLottery({"from": account})
    # enter lottery
    lottery.enterLottery({"from": account, "value": lottery.getEntranceFee()})
    # to end the lottery you have to fund it with
    # some link toekn to access the chainlink node
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    # check that its calculating the winner(lottery_state)
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    if network.show_active() not in local_dev_env:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enterLottery({"from": account, "value": lottery.getEntranceFee()})
    lottery.enterLottery(
        {"from": get_account(index=1), "value": lottery.getEntranceFee()}
    )
    lottery.enterLottery(
        {"from": get_account(index=2), "value": lottery.getEntranceFee()}
    )
    fund_with_link(lottery)
    transaction = lottery.endLottery({"from": account})
    # the below line is possible bcos of the `emit` and event
    # initialized in the .sol file
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    # below we are mocking connecting to a chainlink node and accessing
    # the callbackwithrandomness function that takes in the requestId,
    # a random number and contract address as parameters, it's a use case for our test file
    # basically how we dummy getting a response(mocking responses) from the chainlink node
    static_rng = 777  # _randomness
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, static_rng, lottery.address, {"from": account}
    )
    starting_balance_of_account = account.balance()
    final_balance_of_lottery = lottery.balance()
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + final_balance_of_lottery
