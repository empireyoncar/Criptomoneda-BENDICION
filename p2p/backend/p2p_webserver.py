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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)
