pragma solidity >0.5.0;


contract Transaction {

    string[] public stock;
    uint[] public shares;
    uint[] public money;


    constructor() public {

    }


    function setLatestTransaction(string memory _stock, uint _shares, uint _money) public {

        stock.push(_stock);
        shares.push(_shares);
        money.push(_money);

    }


    function getLatestStock() view public returns (string memory) {

        return stock[stock.length - 1];

    }

    function getLatestShares() view public returns (uint) {

        return shares[stock.length - 1];

    }

    function getLatestMoney() view public returns (uint) {

        return money[stock.length - 1];

    }

    function getLength() view public returns (uint) {
        return stock.length;
    }

}