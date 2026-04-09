# Arquitectura: Blockchain + Wallet + Frontend

## 🏗️ Estructura General

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (HTML/JS)                     │
│     blockchain.html (explorer)    +    wallet.html          │
└──────────────┬─────────────────────────────────┬────────────┘
               │                                 │
        ┌──────▼─────────────────────┐      ┌──────▼──────────┐
        │   BLOCKCHAIN BACKEND       │      │  WALLET BACKEND  │
        │   (Port 5004)              │      │  (Port 5002)     │
        │                            │      │                  │
        │  blockchain_server.py      │      │ wallet_server.py │
        │  • /chain                  │      │ • /generate_wallet│
        │  • /wallet/<addr>/nonce    │      │ • /user_wallet   │
        │  • /send_tx (+ signature)  │      │ • /wallet_info   │
        │  • /mint                   │      │                  │
        │  • /initialize_supply      │      └──────────────────┘
        │  • /commit                 │
        │  • /stats                  │
        └──────┬─────────────────────┘
               │
        ┌──────▼──────────────────────┐
        │   BLOCKCHAIN CORE           │
        │   (blockchain.py)           │
        │                             │
        │  • Block class              │
        │  • Blockchain class         │
        │  • Wallets dict             │
        │  • Pending TX pool          │
        │  • Nonce tracking           │
        └──────┬──────────────────────┘
               │
        ┌──────▼──────────────────────┐
        │   CRYPTO MODULE             │
        │   (criptografia/)           │
        │                             │
        │  • blockchain_crypto.py:    │
        │    - hash_sha256()          │
        │    - hash_bloque()          │
        │  • firma_digital.py:        │
        │    - verificar_firma()      │
        │    - firmar_transaccion()   │
        └─────────────────────────────┘
```

---

## 🔌 Integración Frontend ↔ Backend

### Blockchain Frontend → Blockchain Backend

**File: `Blockchain/frontend/blockchain.html`**

```javascript
// 1. Initialize
const BLOCKCHAIN_API = "http://localhost/CriptoBendicion/blockchain_api";

// 2. Get chain
async function getChain() {
    const response = await fetch(`${BLOCKCHAIN_API}/chain`);
    return await response.json();
}

// 3. Get wallet info (balance + nonce)
async function getWalletInfo(address) {
    const response = await fetch(`${BLOCKCHAIN_API}/wallet/${address}`);
    return await response.json();
}

// 4. Get pending transactions
async function getPending() {
    const response = await fetch(`${BLOCKCHAIN_API}/pending`);
    return await response.json();
}

// 5. Explorer: show blocks, txs, stats
async function displayBlockchain() {
    const chain = await getChain();
    const stats = await fetch(`${BLOCKCHAIN_API}/stats`).then(r => r.json());
    
    // Render chain, show transactions, balance lookup, etc.
}
```

**Endpoints Available:**
- `GET /chain` - full blockchain
- `GET /pending` - txs in mempool
- `GET /block/<hash>` - specific block
- `GET /tx/<hash>` - specific tx
- `GET /wallet/<addr>` - balance, locked, nonce
- `GET /wallet/<addr>/history` - tx history
- `GET /wallet/<addr>/nonce` - just nonce
- `GET /stats` - chain statistics
- `GET /validate` - chain validity

---

### Wallet Frontend → Wallet Backend

**File: `wallet/frontend/wallet.html`**

```javascript
// 1. Initialize
const WALLET_API = "http://localhost/CriptoBendicion/wallet_api";
const BLOCKCHAIN_API = "http://localhost/CriptoBendicion/blockchain_api";

// 2. Generate wallet for user
async function generateWallet(userId) {
    const response = await fetch(`${WALLET_API}/generate_wallet`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
    });
    return await response.json();
    // Returns: { address, public_key_hex, private_key_hex }
}

// 3. Get wallet info
async function getWalletInfo(userId) {
    const response = await fetch(`${WALLET_API}/user_wallet/${userId}`);
    return await response.json();
}

// 4. Send transaction
async function sendTransaction(wallet, receiver, amountSatichis) {
    // Step 1: Get nonce
    const nonce_resp = await fetch(`${BLOCKCHAIN_API}/wallet/${wallet.address}/nonce`);
    const { nonce } = await nonce_resp.json();
    
    // Step 2: Build TX
    const tx_data = {
        from: wallet.address,
        to: receiver,
        amount: amountSatichis,
        nonce: nonce
    };
    
    // Step 3: Sign TX (done on client-side)
    const signature = wallet_library.sign_transaction(wallet.private_key_hex, tx_data);
    
    // Step 4: Send to blockchain
    const response = await fetch(`${BLOCKCHAIN_API}/send_tx`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            tx: {
                ...tx_data,
                public_key: wallet.public_key_hex,
                signature: signature
            }
        })
    });
    return await response.json();
}

// 5. Display wallet state
async function displayWallet(userId) {
    const wallet = await getWalletInfo(userId);
    const balance_resp = await fetch(`${BLOCKCHAIN_API}/wallet/${wallet.address}`);
    const balance_info = await balance_resp.json();
    
    // Show: address, balance (convert satichis to monedas), nonce, etc.
}
```

**Endpoints Available:**
- `GET /user_wallet/<user_id>` - get wallet for user
- `GET /wallet_info/<address>` - full wallet details (private + public key)
- `POST /generate_wallet` - create new wallet

---

## 📊 Data Flow: User Sends Transaction

```
┌─────────────────────────────────────────────────────────┐
│ 1. USER CLICKS "SEND"                                   │
│    wallet.html shows form: [to, amount]                │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 2. FRONTEND GETS NONCE                                  │
│    GET /blockchain_api/wallet/{address}/nonce           │
│    → {"nonce": 5}                                       │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 3. FRONTEND BUILDS TX                                   │
│    {                                                     │
│      "from": wallet.address,                            │
│      "to": user_receiver,                               │
│      "amount": 1000000000,  // 10 monedas              │
│      "nonce": 5                                         │
│    }                                                     │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 4. FRONTEND SIGNS (client-side, private key stays safe)│
│    Signature = ECDSA_sign(TX, wallet.private_key_hex)   │
│    → signature_hex = \"a3b4c5...\"                        │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 5. FRONTEND SENDS TO BLOCKCHAIN                         │
│    POST /blockchain_api/send_tx                         │
│    {                                                     │
│      \"tx\": {                                            │
│        ...tx_data,                                       │
│        \"public_key\": wallet.public_key_hex,             │
│        \"signature\": signature_hex                       │
│      }                                                   │
│    }                                                     │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 6. BLOCKCHAIN VALIDATES                                 │
│    ✓ public_key → address match                        │
│    ✓ Signature valid (ECDSA verify)                    │
│    ✓ Nonce == expected (5)                             │
│    ✓ Balance >= amount                                 │
│    → TX added to pending_transactions                  │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 7. USER CLICKS \"CREATE BLOCK\" (or auto at 1000 TX)      │
│    POST /blockchain_api/commit                          │
│    → New block sealed, TX confirmed, nonce++           │
└────────────┬────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────┐
│ 8. FRONTEND REFRESHES                                   │
│    GET /blockchain_api/wallet/{address}                │
│    → balance decreased, nonce incremented               │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Wallet Compatibility

Your wallet module isNOW **100% compatible** with blockchain:

### Field Names (Updated)
```python
# OLD (incompatible):
wallet = {
    "private_key": "...",   # ❌
    "public_key": "...",    # ❌
    "address": "..."
}

# NEW (compatible):
wallet = {
    "private_key_hex": "...",   # ✅
    "public_key_hex": "...",    # ✅
    "address": "..."            # ✅
}
```

### New Helper Function
```python
# Build and sign TX in one call:
complete_tx = build_and_sign_tx(
    wallet=wallet,
    receiver="address_destino",
    amount=1_000_000_000,  # satichis
    nonce=5,
    tx_id="optional",
    metadata={"memo": "payment"}
)
# Returns: {from, to, amount, nonce, public_key, signature}
# Ready to send to /send_tx
```

---

## 🌐 External Wallet Compatibility

**YES, absolutely.** Your blockchain can be used with ANY wallet if it:

1. **Generates ECDSA keypairs** on SECP256k1 curve
2. **Derives address** as `SHA256(public_key_hex)`
3. **Signs TX** with canonical JSON payload
4. **Follows TX format**: `from, to, amount, nonce, public_key, signature`

### Example: MetaMask-like External Wallet

```javascript
// External wallet (not Bendición, but compatible)
const externalWallet = {
    address: "0xabcd...",
    publicKey: "0x1234...",
    privateKey: "preserved_securely_client_side"
};

// Can send to your blockchain:
const tx = {
    from: externalWallet.address,
    to: "0x9999...",
    amount: 500_000_000,
    nonce: 3,
    public_key: externalWallet.publicKey,
    signature: external_sign_function(tx_data, externalWallet.privateKey)
};

// POST to your blockchain:
fetch("https://your-blockchain.com/send_tx", {
    method: "POST",
    body: JSON.stringify({ tx })
});
```

**Key:** As long as the **signature verifies** with the public_key, the blockchain doesn't care where the wallet comes from.

---

## 💰 Initial Supply: 10,000 Monedas

### How It's Stored

**Treasury Address (System):**
```
Address: "0x00000000000000000000000000000000TREASURY"
Balance: 10,000,000,000,000 satichis (10,000 monedas)
Owner: SYSTEM (no private key)
```

### How To Create It

**One-time setup:**
```bash
POST /blockchain_api/initialize_supply

Response:
{
  "message": "Initial supply created",
  "treasury_address": "0x00000000000000000000000000000000TREASURY",
  "total_monedas": 10000,
  "total_satichis": 1000000000000,
  "block_index": 1
}
```

### How To Distribute To Validators/Nodes

```bash
# From treasury to validator_wallet_1 (5000 monedas)
POST /blockchain_api/mint
{
  "address": "validator_wallet_1_address",
  "amount": 500_000_000_000  # 5000 monedas in satichis
}

# From treasury to validator_wallet_2 (3000 monedas)
POST /blockchain_api/mint
{
  "address": "validator_wallet_2_address",
  "amount": 300_000_000_000  # 3000 monedas in satichis
}

# From treasury to validator_wallet_3 (2000 monedas)
POST /blockchain_api/mint
{
  "address": "validator_wallet_3_address",
  "amount": 200_000_000_000  # 2000 monedas in satichis
}

# Then commit when ready
POST /blockchain_api/commit
```

### Storage Location

In `blockchain.json` (or PostgreSQL later):
```json
{
  "wallets": {
    "0x00000000000000000000000000000000TREASURY": 1000000000000,
    "validator_wallet_1_address": 500000000000,
    "validator_wallet_2_address": 300000000000,
    "validator_wallet_3_address": 200000000000
  }
}
```

---

## 🚀 To Connect Frontend

### Blockchain Frontend
1. In `Blockchain/frontend/blockchain.html`
2. Add JavaScript that fetches from `GET /blockchain_api/chain`, `/stats`, etc.
3. Display chain explorer: blocks, txs, balance lookup

### Wallet Frontend
1. In `wallet/frontend/wallet.html`
2. Add JavaScript that:
   - Calls `POST /wallet_api/generate_wallet` to create wallet
   - Shows private_key_hex (user copies to secure location)
   - Provides UI to send TX
   - On send: fetch nonce, build TX, sign CLIENT-SIDE, POST to `/blockchain_api/send_tx`

Both are **JavaScript in browser**, blockchain/wallet backends provide **REST APIs**.

