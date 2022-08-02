// SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    address payable public recentWinner;
    uint256 public usdEntryFee;
    uint256 public randomness;
    AggregatorV3Interface internal priceFeed;
    // user-defined type like struct
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyhash; // uniquely identify the chainlink vrf node
    event RequestedRandomness(bytes32 requestId);

    // parameters needed to make use of the vrfconsumerbase
    // vrfcoordinator
    // link token i.e link
    // fee
    // hash
    // all of this is gotten in chainlink documentation(randomness)
    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        // amount fee($50) in wei;
        // 50 X 10^18
        usdEntryFee = 50 * (10**18);
        priceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
        fee = _fee;
        keyhash = _keyhash;
    }

    function enterLottery() public payable {
        require(lottery_state == LOTTERY_STATE.OPEN, "The lottery isn't open!");
        // minimum entry fee of $50
        require(
            msg.value >= getEntranceFee(),
            "You don't have enough eth to enter!"
        );
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        // we are setting the price at $50, 2000/ETH
        // first we convert int to uint256
        uint256 adjustedPrice = uint256(price) * 10**10;
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "can't start this lottery yet"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        // uint256(
        //     keccak256(
        //         abi.encodePacked(
        //             nonce,
        //             msg.sender,
        //             block.dificulty,
        //             block.timestamp
        //         )
        //     )
        // ) % players.length;
        // mind you the commented block above returns
        // a random value but it is not secure. things like the
        // block.difficulty, timestamp are prediactable or can be changed
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        // you request true randomness with this
        bytes32 requestId = requestRandomness(keyhash, fee);
        // added the below for catching event;
        // after initialzing with type event RequestRandomness();
        // to get the the event on the node and passed in the
        // request id as input parameter
        emit RequestedRandomness(requestId);
        // after the above line, in the tests file
        // end_the_lottery in a (varaiable)
        // you can access data from this variable now i.e events
        // requestId = [variablename].events["RequestRandomness"]["requestId"]
    }

    // request, response, we wait for the oracle to return ?
    // we want only our vrfCoordinator to be albe to call this function
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "you aren't there yet"
        );

        require(_randomness > 0, "random-winner-found");

        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);
        // RESET players array
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
