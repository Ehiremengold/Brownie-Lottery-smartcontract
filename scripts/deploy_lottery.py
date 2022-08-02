from brownie import config, network, Lottery
from scripts.utils import get_account, get_contract, fund_with_link
import time


def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Lottery deployed!")
    return lottery


# what are the trhings you want to do wwith this lottery
# 1. start the lottery
# 2. enter the lottery
# 3. end the lottery

# startlottery
def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    startingLottery_tx = lottery.startLottery({"from": account})
    startingLottery_tx.wait(1)
    print("Lottery started!")


# enterlottery
def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 100000000
    enter_lottery_tx = lottery.enterLottery({"from": account, "value": value})
    enter_lottery_tx.wait(1)
    print("You entered the lottery successfully!")


# endlottery
def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # before ending the lottery we need some link token in this contract
    # this token is used to make request to the oracle for a truly random number.
    # the contract also waits for a response
    tx = fund_with_link(lottery)
    tx.wait(1)
    tx2 = lottery.endLottery({"from": account})
    tx2.wait(1)
    time.sleep(200)
    print(f"{lottery.recentWinner()} is the new winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
