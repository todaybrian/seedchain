from flask import Flask, render_template, url_for, request, redirect
import json

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
    return render_template('dashboard.html', page_title="Dashboard · Seedchain")

@app.route('/browse')
def browse():
    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    if request.args.get('q'):
        query = request.args.get('q')
        d = {k: v for k, v in d.items() if query.lower() in k.lower()}    

    return render_template('browse.html', page_title="Browse · Seedchain", stocks=d)


@app.route('/stock/<name>')
def specific_stock(name):
    with open('static/stocks.json') as f:
        d = json.loads(f.read())

    if name not in d:
        return render_template('404.html'), 404

    return render_template('stock.html', name = name, stocks=d)

# include 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
