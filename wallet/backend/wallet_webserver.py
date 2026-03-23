from flask import Flask
from routeswallet import wallet_web_bp

app = Flask(__name__)

app.register_blueprint(wallet_web_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
