from flask import Blueprint, render_template

wallet_web_bp = Blueprint(
    "wallet_web",
    __name__,
    template_folder="../frontend"
)

@wallet_web_bp.route("/wallet")
def wallet_page():
    return render_template("wallet.html")
