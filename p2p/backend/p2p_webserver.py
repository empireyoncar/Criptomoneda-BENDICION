"""Web server for P2P frontend pages."""

from flask import Flask, render_template
from flask_cors import CORS
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
CORS(app)

app.jinja_loader = ChoiceLoader([
    FileSystemLoader("/app/p2p/frontend"),
])


@app.route("/p2p")
@app.route("/p2p/")
def p2p_home():
    return render_template("p2p.html")


@app.route("/p2p/order/<order_id>")
def p2p_order(order_id: str):
    return render_template("order.html", order_id=order_id)


@app.route("/p2p/chat/<order_id>")
def p2p_chat(order_id: str):
    return render_template("chat.html", order_id=order_id)


@app.route("/p2p/reputation")
def p2p_reputation():
    return render_template("reputacion.html")


@app.route("/p2p/orders-online")
def p2p_orders_online():
    return render_template("ordenesonline.html")


@app.route("/p2p/disputas")
def p2p_disputas():
    return render_template("disputas1.html")


@app.route("/p2p/panel-disputas")
def p2p_panel_disputas():
    return render_template("paneldisputas.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)
