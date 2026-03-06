import bip39 from 'bip39';
import hdkey from 'ethereumjs-wallet/hdkey.js';
import Wallet from 'ethereumjs-wallet';
import CryptoJS from 'crypto-js';
import axios from 'axios';
import { createHash } from 'crypto';
import { ecdsaSign } from 'ethereumjs-util';

const NODE_URL = 'http://147.185.221.25:9197'; // tu nodo vía tunnel

// ------------------- Registro de usuario -------------------
export async function registerUser(username, password, email) {
  // Generar frase semilla HD
  const mnemonic = bip39.generateMnemonic();
  const seed = bip39.mnemonicToSeedSync(mnemonic);
  const hdWallet = hdkey.fromMasterSeed(seed);

  // Derivar primera dirección
  const key = hdWallet.derivePath("m/44'/60'/0'/0/0").getWallet();
  const address = '0x' + key.getAddress().toString('hex');
  const privateKey = key.getPrivateKey().toString('hex');

  // Cifrar la clave privada con la contraseña del usuario
  const encryptedPrivateKey = CryptoJS.AES.encrypt(privateKey, password).toString();

  // Enviar datos al nodo (solo dirección pública)
  await axios.post(`${NODE_URL}/register`, {
    username,
    email,
    address
  });

  return { mnemonic, address, encryptedPrivateKey };
}

// ------------------- Recuperar wallet desde frase semilla -------------------
export function recoverWallet(mnemonic, password) {
  const seed = bip39.mnemonicToSeedSync(mnemonic);
  const hdWallet = hdkey.fromMasterSeed(seed);
  const key = hdWallet.derivePath("m/44'/60'/0'/0/0").getWallet();
  const address = '0x' + key.getAddress().toString('hex');
  const privateKey = key.getPrivateKey().toString('hex');
  const encryptedPrivateKey = CryptoJS.AES.encrypt(privateKey, password).toString();
  return { address, encryptedPrivateKey };
}

// ------------------- Firmar transacción -------------------
export function signTransaction(tx, privateKeyHex) {
  const privateKeyBuffer = Buffer.from(privateKeyHex, 'hex');
  const txHash = createHash('sha256').update(JSON.stringify(tx)).digest();
  const signature = ecdsaSign(txHash, privateKeyBuffer);
  return signature;
}

// ------------------- Enviar transacción al nodo -------------------
export async function sendTransaction(tx, privateKeyHex) {
  const signature = signTransaction(tx, privateKeyHex);

  const response = await axios.post(`${NODE_URL}/send_tx`, {
    tx,
    signature
  });

  return response.data;
}

// ------------------- Consultar saldo -------------------
export async function getBalance(address) {
  const response = await axios.get(`${NODE_URL}/balance/${address}`);
  return response.data.balance;
}

// ------------------- Ejemplo de uso -------------------
(async () => {
  // 1️⃣ Registro
  const user = await registerUser('juan', 'miContraseña123', 'juan@mail.com');
  console.log('Wallet creada:', user);

  // 2️⃣ Crear una transacción
  const tx = {
    from: user.address,
    to: '0xABCDEF1234567890',
    amount: 10
  };

  // 3️⃣ Desencriptar clave privada para firmar
  const privateKey = CryptoJS.AES.decrypt(user.encryptedPrivateKey, 'miContraseña123').toString(CryptoJS.enc.Utf8);

  // 4️⃣ Enviar transacción al nodo
  const result = await sendTransaction(tx, privateKey);
  console.log('Transacción enviada:', result);

  // 5️⃣ Consultar saldo actualizado
  const balance = await getBalance(user.address);
  console.log('Saldo actual:', balance);
})();

