pragma solidity >0.5.0;


contract LatestTransaction {

    string public stock;
    uint public shares;


    constructor() public {

        stock = 'test';
        shares = 0;

    }


    function setLatestTransaction(string memory _stock, uint _shares) public {

        stock = _stock;
        shares = _shares;

    }


    function getLatestTransaction() view public returns (string memory) {

        return stock;

    }

}