from brownie import network
import pytest
from scripts.utils import get_account, local_dev_env, fund_with_link
from scripts.deploy_lottery import deploy_lottery
import time


def test_can_pick_winner():
    if network.show_active() in local_dev_env:
        pytest.skip()
    account = get_account()
    lottery = deploy_lottery()
    lottery.startLottery({"from": account})
    lottery.enterLottery({"from": account, "value": lottery.getEntranceFee()})
    lottery.enterLottery({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    time.sleep(200)
    assert lottery.recentWinner() == account
    # above line of code returns an error
    # assertion error
    # lottery.recentWinner() returns 0x000...
    # account returns the account if account else get_account
    # so lottery.recentWinner != account
    assert lottery.balance() == 0
