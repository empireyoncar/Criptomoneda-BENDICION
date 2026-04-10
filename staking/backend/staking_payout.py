import requests
import time
import uuid

from staking_db import (
    create_payout,
    list_payout_stake_ids,
    list_pending_rewards,
    mark_reward_error,
    mark_reward_paid,
)

# MISMO ENDPOINT QUE USA EL FRONTEND
DON_API_URL = "https://empireyoncar.duckdns.org/CriptoBendicion/don_api/don/add"
def process_payouts():
    recompensas = list_pending_rewards()

    # evitar pagos duplicados
    pagados = list_payout_stake_ids()

    for item in recompensas:
        stake_id = item.get("stake_id")
        if not stake_id:
            continue

        if stake_id in pagados:
            mark_reward_paid(stake_id, int(item.get("paid_timestamp") or time.time()))
            continue

        user_id = item.get("user_id")
        reward = item.get("reward_don")
        if reward is None:
            reward = item.get("reward")

        if not user_id or reward is None:
            continue

        try:
            reward = float(reward)
        except (TypeError, ValueError):
            mark_reward_error(stake_id, "reward_invalido", int(time.time()))
            continue

        if reward <= 0:
            mark_reward_error(stake_id, "reward_no_positivo", int(time.time()))
            continue

        # PAGAR DON
        try:
            res = requests.post(DON_API_URL, json={
                "user_id": user_id,
                "amount": reward,
                "metadata": {
                    "source": "staking_recompensa",
                    "stake_id": stake_id,
                    "reward_timestamp": item.get("timestamp")
                }
            }, timeout=15)
            res.raise_for_status()
            try:
                api_response = res.json()
            except ValueError:
                api_response = {"raw": res.text}
        except Exception as e:
            print("Error pagando DON:", e)
            mark_reward_error(stake_id, str(e), int(time.time()))
            continue

        # CAMBIAR ESTADO A PAID
        paid_timestamp = int(time.time())
        mark_reward_paid(stake_id, paid_timestamp)

        # REGISTRAR LOG DE PAGO
        create_payout({
            "payout_id": str(uuid.uuid4()),
            "stake_id": stake_id,
            "user_id": user_id,
            "wallet": item.get("wallet"),
            "amount": reward,
            "asset": "DON",
            "status": "paid",
            "created_timestamp": int(item.get("timestamp", time.time())),
            "paid_timestamp": paid_timestamp,
            "source": "staking_recompensa",
            "reward_record_timestamp": item.get("timestamp"),
            "transfer_tx_id": item.get("transfer_tx_id"),
            "don_api": {
                "http_status": "OK",
                "response_body": api_response,
                "tx_id": api_response.get("tx_id") if isinstance(api_response, dict) else None
            },
            "idempotency_key": f"stake:{stake_id}",
            "support_note": "Pago automatico por vencimiento de staking"
        })


if __name__ == "__main__":
    process_payouts()
