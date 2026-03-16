# blockchain.py
import time
import json
from hashlib import sha256


class Block:
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()

        return sha256(block_string).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.wallets = {}  # address -> balance

        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, time.time(), [], "0")
        self.chain.append(genesis)

    def get_last_block(self):
        return self.chain[-1]

    def create_wallet(self, address):
        if address not in self.wallets:
            self.wallets[address] = 0.0

    def get_balance(self, address):
        return float(self.wallets.get(address, 0.0))

    def add_transaction(self, sender, receiver, amount):
        amount = float(amount)

        # Crear wallets si no existen
        self.create_wallet(sender)
        self.create_wallet(receiver)

        # PERMITIR que SYSTEM emita monedas sin saldo
        if sender != "SYSTEM" and self.wallets[sender] < amount:
            return False

        tx = {
            "from": sender,
            "to": receiver,
            "amount": amount
        }

        self.pending_transactions.append(tx)
        return True

    def commit_pending_transactions(self):
        """Crea un bloque nuevo sin minería."""
        if not self.pending_transactions:
            return None

        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.hash
        )

        # Aplicar transacciones
        for tx in self.pending_transactions:
            sender = tx["from"]
            receiver = tx["to"]
            amount = float(tx["amount"])

            # SYSTEM no pierde saldo al emitir
            if sender != "SYSTEM":
                self.wallets[sender] -= amount

            self.wallets[receiver] += amount

        self.pending_transactions = []
        self.chain.append(new_block)
        return new_block
