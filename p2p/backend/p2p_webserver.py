"""Web server for P2P frontend pages."""

from flask import Flask, abort, render_template, send_file, send_from_directory
from flask_cors import CORS
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
CORS(app)

VENDOR_FILES = {"elliptic.min.js", "crypto-js.min.js"}


@app.after_request
def set_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https:; "
        "connect-src 'self' https: http: ws: wss:; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

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


@app.route("/p2p/calificacion/<order_id>")
def p2p_calificacion(order_id: str):
    return render_template("calificacion.html", order_id=order_id)


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


@app.route("/p2p/seguridad/guard.js")
@app.route("/CriptoBendicion/p2p/seguridad/guard.js")
def p2p_security_guard_js():
    return send_file("/app/seguridad/frontend/guard.js", mimetype="application/javascript")


@app.route("/seguridad/vendor/<path:filename>")
@app.route("/CriptoBendicion/seguridad/vendor/<path:filename>")
def p2p_security_vendor_js(filename):
    if filename not in VENDOR_FILES:
        abort(404)
    return send_from_directory("/app/seguridad/frontend/vendor", filename, mimetype="application/javascript")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)
