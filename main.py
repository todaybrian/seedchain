from flask import Flask, render_template, url_for, request, redirect
import json
from web3 import Web3
from solcx import compile_source

app = Flask(
  __name__,
  template_folder='templates',
  static_folder='static'
)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    success = request.args.get('success', False)
    personal_data = {}
    current_prices = {}
    with open('static/stocks.json') as f:
        ad = json.loads(f.read())
        for name in ad:
            current_prices[name] = ad[name]['price']

    with open('static/owned.json') as f:
        aad = json.loads(f.read())
        personal_data = {}
        for name in aad:
            personal_data[name] = {'shares': 0, 'net': 0, 'percent': 0, 'current_price': 0}
            ad = aad[name]
            personal_data[name]['shares'] = ad['shares']
            personal_data[name]['net'] = (current_prices[name] - ad['price_bought']) * ad['shares']
            personal_data[name]['percent'] = (current_prices[name] * ad['shares'] - ad['price_bought'] * ad['shares']) / (ad['price_bought'] * ad['shares'])
            personal_data[name]['current_price'] = current_prices[name]

    # w3 = Web3(Web3.EthereumTesterProvider())

    # with open('static/address.txt') as f:
    #     address = f.read()
    # with open('static/project.sol') as f:
    #     compiled_sol = compile_source(f.read(), output_values=['abi', 'bin'])
    #     contract_id, contract_interface = compiled_sol.popitem()
    #     bytecode = contract_interface['bin']

    #     # get abi

    #     abi = contract_interface['abi']

    # print(address, abi)

    # contract_instance = w3.eth.contract(address=address, abi=abi) 

    # print(contract_instance)

    # print(contract_instance.functions.getLatestStock().call())  

    return render_template('dashboard.html', page_title="Dashboard · Seedchain", success=success, personal_data=personal_data)


@app.route('/browse')
def browse():
    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    if request.args.get('q'):
        query = request.args.get('q')
        d = {k: v for k, v in d.items() if query.lower() in k.lower()}    

    return render_template('browse.html', page_title="Browse · Seedchain", stocks=d)


@app.route('/stock/<name>', methods=['GET', 'POST'])
def specific_stock(name):
    not_enough_buy = False
    not_enough_sell = False

    current_price = 0
    with open('static/stocks.json') as f:
        current_price = json.loads(f.read())[name]['price']

    with open('static/owned.json') as f:
        ad = json.loads(f.read())
        personal_data = {'shares': 0, 'net': 0, 'percent': 0}
        if name in ad:
            ad = ad[name]
            personal_data['shares'] = ad['shares']
            personal_data['net'] = (current_price - ad['price_bought']) * ad['shares']
            personal_data['percent'] = (current_price * ad['shares'] - ad['price_bought'] * ad['shares']) / (ad['price_bought'] * ad['shares'])


    if request.method == 'POST':
        # the user selected instant buy, not bid buy
        if 'instant-buy' in request.form:
            amount = int(request.form['number'])
            # get the dict of all the available bid sell values
            with open('static/sellreq.json') as f:
                try:
                    sell = json.loads(f.read())[name]
                except KeyError:
                    sell = []
            total_shares = sum(val['share_count'] for val in sell)
            if total_shares < amount:
                not_enough_buy = True
            else:
                return redirect(url_for('instant_buy', name=name, shares=amount))
                    # the user selected instant buy, not bid buy
        if 'instant-sell' in request.form:
            amount = int(request.form['number'])
            # get the dict of all the available bid sell values
            with open('static/buyreq.json') as f:
                try:
                    sell = json.loads(f.read())[name]
                except KeyError:
                    sell = []
            total_shares = sum(val['share_count'] for val in sell)
            if total_shares < amount:
                not_enough_sell = True
            # the person must also have "amount" number of stocks
            with open('static/owned.json') as f:
                owned = json.loads(f.read())[name]['shares']
                if owned < amount:
                    not_enough_sell = True
            if not not_enough_sell:
                return redirect(url_for('instant_sell', name=name, shares=amount))
                

        if 'bid-buy' in request.form:
            return redirect(url_for('bid_buy', name=name, shares=request.form['number'], price=request.form['price']))
        if 'bid-sell' in request.form:
            with open('static/owned.json') as f:
                owned = json.loads(f.read())[name]['shares']
                if owned < int(request.form['number']):
                    not_enough_sell = True
                else:
                    return redirect(url_for('bid_sell', name=name, shares=request.form['number'], price=request.form['price']))
            
    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    if name not in d:
        return render_template('404.html'), 404
        
    with open('static/buyreq.json') as f:
        try:
            buyreq = sorted(json.loads(f.read())[name], key=lambda d: -d['price'])[:5]
        except KeyError:
            buyreq = []

    with open('static/sellreq.json') as f:
        try:
            sellreq = sorted(json.loads(f.read())[name], key=lambda d: d['price'])[:5]
            print(sellreq)
        except KeyError:
            sellreq = []        
        
    return render_template('stock.html', personal_data=personal_data, name = name, stocks=d, not_enough_buy=not_enough_buy, not_enough_sell=not_enough_sell, buyreq=buyreq, sellreq=sellreq, page_title=f"{name} - {d[name]['founder']} · Seedchain")

@app.route('/order/<name>/instant-buy/<shares>', methods=['GET', 'POST'])
def instant_buy(name, shares):
    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    # check if shares is an integer
    if not shares.isdigit():
        return render_template('404.html'), 404
    
    shares = int(shares)

    if name not in d:
        return render_template('404.html'), 404
    
    tot_price = 0

    tot = 0

    with open('static/sellreq.json') as f:
        sellreq = sorted(json.loads(f.read())[name], key=lambda d: d['price'])

    for i in range(len(sellreq)):
        tot += sellreq[i]['share_count']
        if tot == shares:
            tot_price += sellreq[i]['price'] * sellreq[i]['share_count']
            new_price = sellreq[i]['price']
            break
        elif tot > shares:
            tot_price += sellreq[i]['price'] * (sellreq[i]['share_count'] - (tot - shares))
            sellreq[i]['share_count'] = tot - shares
            new_price = sellreq[i]['price']
            break
        tot_price += sellreq[i]['price'] * sellreq[i]['share_count']
    
    if request.method == 'POST':
    # get the dict, sort by price, run loop for 
    # howmuchever is needed, delete those objects 
    # and make all them zero except last one (subtract),
    # set new price of the stock to be latest stocks.json
    # later, add it to current stocks owned by that person
        with open('static/sellreq.json') as f:
            sellreq = sorted(json.loads(f.read())[name], key=lambda d: d['price'])
        
        sellreqcopy = []

        tot = 0

        ignore = set()

        new_price = 0

        tot_price = 0

        for i in range(len(sellreq)):
            tot += sellreq[i]['share_count']
            if tot == shares:
                tot_price += sellreq[i]['price'] * sellreq[i]['share_count']
                ignore.add(i)
                new_price = sellreq[i]['price']
                break
            elif tot > shares:
                tot_price += sellreq[i]['price'] * (sellreq[i]['share_count'] - (tot - shares))
                sellreq[i]['share_count'] = tot - shares
                new_price = sellreq[i]['price']
                break
            tot_price += sellreq[i]['price'] * sellreq[i]['share_count']
            ignore.add(i)
        
        for i in range(len(sellreq)):
            if i not in ignore:
                sellreqcopy.append(sellreq[i])

        with open('static/sellreq.json', 'r+') as f:
            all_val = json.loads(f.read())
            f.truncate(0)
            if len(sellreqcopy) > 0:
                all_val[name] = sellreqcopy
            else:
                del all_val[name]
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))

        with open('static/stocks.json', 'r+') as f:
            all_val = json.loads(f.read())
            all_val[name]['price'] = new_price
            f.truncate(0)
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))

        # add to personal user's stock collection lol
        with open('static/owned.json', 'r+') as f:
            all_val = json.loads(f.read())
            if name in all_val:
                print(tot_price, shares)
                all_val[name]['price_bought'] = (all_val[name]['price_bought'] * all_val[name]['shares'] + tot_price) / (all_val[name]['shares'] + shares)
                all_val[name]['shares'] += shares
            else:
                print(tot_price, shares)
                all_val[name] = {}
                all_val[name]['price_bought'] = tot_price / shares
                all_val[name]['shares'] = shares
            f.truncate(0)
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))

            with open('static/project.sol') as f:
                compiled_sol = compile_source(f.read(), output_values=['abi', 'bin'])
                contract_id, contract_interface = compiled_sol.popitem()
                bytecode = contract_interface['bin']

                # get abi

                abi = contract_interface['abi']

                # web3.py instance

                w3 = Web3(Web3.EthereumTesterProvider())

                # set pre-funded account as sender

                w3.eth.default_account = w3.eth.accounts[0]

                Transaction = w3.eth.contract(abi=abi, bytecode=bytecode)

                # Submit the transaction that deploys the contract

                tx_hash = Transaction.constructor().transact()

                tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                transaction = w3.eth.contract(

                    address=tx_receipt.contractAddress,

                    abi=abi

                )

                print(tx_receipt.contractAddress, abi)

                tx_hash = transaction.functions.setLatestTransaction(name, shares, int(tot_price / shares)).transact()

                tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                print(transaction.functions.getLatestStock().call())
                print(transaction.functions.getLength().call())
            

        return redirect(url_for('dashboard', success=True))

    return render_template('order-buy.html', name=name, shares=shares, tot_price=round(tot_price, 2), order_desc="Instant Buy")

@app.route('/order/<name>/bid-buy/<shares>/<price>', methods=['GET', 'POST'])
def bid_buy(name, shares, price):

    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    # check if shares is an integer
    if not shares.isdigit():
        return render_template('404.html'), 404
    
    if name not in d:
        return render_template('404.html'), 404
    
    shares = int(shares)
    price = float(price)

    if request.method == 'POST':
        # add to json file, thats about it. do not add to shares bought and all
        with open('static/buyreq.json', 'r+') as f:
            all_val = json.loads(f.read())
            all_val[name] = all_val.get(name, []) + [{"price": price, "share_count": shares}]
            f.truncate(0)
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))
        return redirect(url_for('dashboard', success=True))

    return render_template('order-buy.html', name=name, shares=shares, tot_price=round(price * shares, 2), order_desc="Bid Buy")


@app.route('/order/<name>/instant-sell/<shares>', methods=['GET', 'POST'])
def instant_sell(name, shares):
    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    # check if shares is an integer
    if not shares.isdigit():
        return render_template('404.html'), 404
    
    shares = int(shares)

    if name not in d:
        return render_template('404.html'), 404
    
    tot_price = 0

    tot = 0

    with open('static/buyreq.json') as f:
        buyreq = sorted(json.loads(f.read())[name], key=lambda d: -d['price'])

    for i in range(len(buyreq)):
        tot += buyreq[i]['share_count']
        if tot == shares:
            tot_price += buyreq[i]['price'] * buyreq[i]['share_count']
            new_price = buyreq[i]['price']
            break
        elif tot > shares:
            tot_price += buyreq[i]['price'] * (buyreq[i]['share_count'] - (tot - shares))
            buyreq[i]['share_count'] = tot - shares
            new_price = buyreq[i]['price']
            break
        tot_price += buyreq[i]['price'] * buyreq[i]['share_count']
    
    if request.method == 'POST':
    # get the dict, sort by price, run loop for 
    # howmuchever is needed, delete those objects 
    # and make all them zero except last one (subtract),
    # set new price of the stock to be latest stocks.json
    # later, add it to current stocks owned by that person
        with open('static/buyreq.json') as f:
            buyreq = sorted(json.loads(f.read())[name], key=lambda d: -d['price'])

        with open('static/owned.json', 'r+') as f:
            all_val = json.loads(f.read())
            all_val[name]['shares'] -= shares
            if all_val[name]['shares'] == 0:
                del all_val[name]
            f.truncate(0)
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))

        
        buyreqcopy = []

        tot = 0

        ignore = set()

        new_price = 0

        tot_price = 0

        for i in range(len(buyreq)):
            tot += buyreq[i]['share_count']
            if tot == shares:
                tot_price += buyreq[i]['price'] * buyreq[i]['share_count']
                ignore.add(i)
                new_price = buyreq[i]['price']
                break
            elif tot > shares:
                tot_price += buyreq[i]['price'] * (buyreq[i]['share_count'] - (tot - shares))
                buyreq[i]['share_count'] = tot - shares
                new_price = buyreq[i]['price']
                break
            tot_price += buyreq[i]['price'] * buyreq[i]['share_count']
            ignore.add(i)
        
        for i in range(len(buyreq)):
            if i not in ignore:
                buyreqcopy.append(buyreq[i])

        with open('static/buyreq.json', 'r+') as f:
            all_val = json.loads(f.read())
            f.truncate(0)
            if len(buyreqcopy) > 0:
                all_val[name] = buyreqcopy
            else:
                del all_val[name]
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))

        with open('static/stocks.json', 'r+') as f:
            all_val = json.loads(f.read())
            all_val[name]['price'] = new_price
            f.truncate(0)
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))

        return redirect(url_for('dashboard', success=True))

    return render_template('order-buy.html', name=name, shares=shares, tot_price=round(tot_price, 2), order_desc="Instant Sell")



@app.route('/order/<name>/bid-sell/<shares>/<price>', methods=['GET', 'POST'])
def bid_sell(name, shares, price):

    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    # check if shares is an integer
    if not shares.isdigit():
        return render_template('404.html'), 404
    
    if name not in d:
        return render_template('404.html'), 404
    
    shares = int(shares)
    price = float(price)

    if request.method == 'POST':
        # add to json file, thats about it. do not add to shares bought and all
        with open('static/sellreq.json', 'r+') as f:
            all_val = json.loads(f.read())
            all_val[name] = all_val.get(name, []) + [{"price": price, "share_count": shares}]
            f.truncate(0)
            f.seek(0)
            f.write(json.dumps(all_val, indent=4))
        return redirect(url_for('dashboard', success=True))

    return render_template('order-buy.html', name=name, shares=shares, tot_price=round(price * shares, 2), order_desc="Bid Sell")


# include 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
