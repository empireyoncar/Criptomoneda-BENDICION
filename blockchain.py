import hashlib
import time
import json
import os
import rsa  # pip install rsa

CHAIN_FILE = "blockchain.json"
DIFFICULTY = 3  # dificultad para prueba de trabajo (opcional)

# -----------------------------
# Clase Bloque
# -----------------------------
class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions  # lista de transacciones
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.transactions}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(str(block_string).encode()).hexdigest()

# -----------------------------
# Blockchain
# -----------------------------
class Blockchain:
    def __init__(self, mining=False):
        self.chain = self.load_chain() or [self.create_genesis_block()]
        self.pending_transactions = []
        self.balances = {}
        self.wallets = {}  # wallet_name -> (public_key, private_key)
        self.mining = mining

    def create_genesis_block(self):
        return Block(0, time.time(), [], "0")

    def get_last_block(self):
        return self.chain[-1]
   
    def get_last_block(self):
        return self.chain[-1]

    # -----------------------------
    # Wallets
    # -----------------------------
    def create_wallet(self, wallet_name):
        public_key, private_key = rsa.newkeys(512)
        self.wallets[wallet_name] = (public_key, private_key)
        self.balances[wallet_name] = 0
        print(f"Wallet '{wallet_name}' creada con saldo 0")
        self.save_chain()
        return wallet_name, public_key, private_key

    def get_balance(self, wallet_name):
        return self.balances.get(wallet_name, 0)

    # -----------------------------
    # Transacciones
    # -----------------------------
    def add_transaction(self, sender, receiver, amount):
        if sender not in self.wallets or receiver not in self.wallets:
            print("Wallet no encontrada")
            return False
        if self.balances[sender] < amount:
            print("Saldo insuficiente")
            return False
        # Firmar transacción
        sender_priv = self.wallets[sender][1]
        tx_str = f"{sender}{receiver}{amount}".encode()
        signature = rsa.sign(tx_str, sender_priv, 'SHA-256')
        self.pending_transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'signature': signature.hex()
        })
        print(f"Transacción agregada: {sender} -> {receiver} : {amount}")
        return True

    def verify_transaction(self, tx):
        sender_pub = self.wallets[tx['sender']][0]
        tx_str = f"{tx['sender']}{tx['receiver']}{tx['amount']}".encode()
        signature = bytes.fromhex(tx['signature'])
        try:
            rsa.verify(tx_str, signature, sender_pub)
            return True
        except:
            return False

    # -----------------------------
    # Minado / bloques
    # -----------------------------
    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.calculate_hash()
        while not computed_hash.startswith("0" * DIFFICULTY):
            block.nonce += 1
            computed_hash = block.calculate_hash()
        return computed_hash

    def mine_block(self):
        if not self.pending_transactions:
            return
        # Verificar transacciones
        valid_transactions = [tx for tx in self.pending_transactions if self.verify_transaction(tx)]
        # Actualizar balances
        for tx in valid_transactions:
            self.balances[tx['sender']] -= tx['amount']
            self.balances[tx['receiver']] += tx['amount']
        last_block = self.get_last_block()
        block = Block(len(self.chain), time.time(), valid_transactions, last_block.hash)
        if self.mining:
            block.hash = self.proof_of_work(block)
        else:
            block.hash = block.calculate_hash()
        self.chain.append(block)
        self.pending_transactions = []
        print(f"Bloque minado: {block.index} Hash: {block.hash}")
        self.save_chain()

    # -----------------------------
    # Guardar / cargar blockchain
    # -----------------------------
    def save_chain(self):
        data = {
            'chain': [block.__dict__ for block in self.chain],
            'balances': self.balances,
            'wallets': {k: (v[0].save_pkcs1().hex(), v[1].save_pkcs1().hex()) for k,v in self.wallets.items()}
        }
        with open(CHAIN_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def load_chain(self):
        if os.path.exists(CHAIN_FILE):
            with open(CHAIN_FILE, "r") as f:
                data = json.load(f)
                self.balances = data.get('balances', {})
                self.wallets = {}
                for k,v in data.get('wallets', {}).items():
                    pub = rsa.PublicKey.load_pkcs1(bytes.fromhex(v[0]))
                    priv = rsa.PrivateKey.load_pkcs1(bytes.fromhex(v[1]))
                    self.wallets[k] = (pub, priv)
                chain = []
                for b in data['chain']:
                    block = Block(b['index'], b['timestamp'], b['transactions'], b['previous_hash'], b['nonce'])
                    block.hash = b['hash']
                    chain.append(block)
                return chain
        return None

# -----------------------------
# Uso
# -----------------------------
if __name__ == "__main__":
    blockchain = Blockchain(mining=False)

    # Crear wallets
    blockchain.create_wallet("Alice")
    blockchain.create_wallet("Bob")

    # Dar saldo inicial a Alice
    blockchain.balances["Alice"] = 100

    # Enviar monedas
    blockchain.add_transaction("Alice", "Bob", 25)
    
    # Minar bloque
    blockchain.mine_block()

    # Mostrar saldos
    print("Saldos:")
    print("Alice:", blockchain.get_balance("Alice"))
    print("Bob:", blockchain.get_balance("Bob"))
