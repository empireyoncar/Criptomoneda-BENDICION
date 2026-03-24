import time
import json
from hashlib import sha256
from blockchain_blocks import load_state, save_state, rotate_if_needed


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
        chain_data, pending, wallets, locked = load_state()

        self.chain = []
        for b in chain_data:
            block = Block(
                index=b["index"],
                timestamp=b["timestamp"],
                transactions=b["transactions"],
                previous_hash=b["previous_hash"]
            )
            block.hash = b["hash"]
            self.chain.append(block)

        self.pending_transactions = pending
        self.wallets = wallets
        self.locked_balances = locked

        if len(self.chain) == 0:
            self.create_genesis_block()
            save_state(self.export_chain(), [], self.wallets, self.locked_balances)

    def export_chain(self):
        return [
            {
                "index": b.index,
                "timestamp": b.timestamp,
                "transactions": b.transactions,
                "previous_hash": b.previous_hash,
                "hash": b.hash
            }
            for b in self.chain
        ]

    def create_genesis_block(self):
        genesis = Block(0, time.time(), [], "0")
        self.chain.append(genesis)

    def get_last_block(self):
        return self.chain[-1]

    def create_wallet(self, address):
        if address not in self.wallets:
            self.wallets[address] = 0.0
        if address not in self.locked_balances:
            self.locked_balances[address] = 0.0

    def get_balance(self, address):
        return float(self.wallets.get(address, 0.0))

    def _get_locked_balance(self, address):
        return float(self.locked_balances.get(address, 0.0))

    def _lock_amount(self, address, amount):
        if address not in self.locked_balances:
            self.locked_balances[address] = 0.0
        self.locked_balances[address] += float(amount)

    def _unlock_amount(self, address, amount):
        if address not in self.locked_balances:
            self.locked_balances[address] = 0.0
        self.locked_balances[address] -= float(amount)
        if self.locked_balances[address] < 0:
            self.locked_balances[address] = 0.0

    def add_transaction(self, sender, receiver, amount):
        amount = float(amount)

        self.create_wallet(sender)
        self.create_wallet(receiver)

        if amount <= 0:
            return False

        if sender != "SYSTEM":
            confirmed = self.wallets[sender]
            locked = self._get_locked_balance(sender)
            available = confirmed - locked
            if available < amount:
                return False

        tx = {"from": sender, "to": receiver, "amount": amount}

        if sender != "SYSTEM":
            self._lock_amount(sender, amount)

        self.pending_transactions.append(tx)

        save_state(self.export_chain(), self.pending_transactions, self.wallets, self.locked_balances)
        return True

    def commit_pending_transactions(self):
        if not self.pending_transactions:
            return None

        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.hash
        )

        for tx in self.pending_transactions:
            sender = tx["from"]
            receiver = tx["to"]
            amount = float(tx["amount"])

            if sender != "SYSTEM":
                self._unlock_amount(sender, amount)
                self.wallets[sender] -= amount

            self.wallets[receiver] += amount

        self.pending_transactions = []
        self.chain.append(new_block)

        save_state(self.export_chain(), self.pending_transactions, self.wallets, self.locked_balances)
        rotate_if_needed(self.export_chain(), self.pending_transactions, self.wallets, self.locked_balances)

        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                return False

            if current.previous_hash != previous.hash:
                return False

        return True
