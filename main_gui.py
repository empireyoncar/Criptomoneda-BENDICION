# main_gui.py
import tkinter as tk
from tkinter import messagebox
from wallets_secure import SecureWallet
from blockchain import Blockchain

blockchain = Blockchain(mining=False)
wallets = {}

class WalletApp:
    def __init__(self, master):
        self.master = master
        master.title("Wallet Segura BENDICION")

        self.wallet = None

        # Crear wallet
        tk.Label(master, text="Nombre Wallet").grid(row=0, column=0)
        self.name_entry = tk.Entry(master)
        self.name_entry.grid(row=0, column=1)

        tk.Label(master, text="Contraseña").grid(row=1, column=0)
        self.pass_entry = tk.Entry(master, show="*")
        self.pass_entry.grid(row=1, column=1)

        tk.Button(master, text="Crear Wallet", command=self.create_wallet).grid(row=2, column=0, columnspan=2)
        tk.Button(master, text="Generar Dirección", command=self.generate_address).grid(row=3, column=0, columnspan=2)
        tk.Button(master, text="Enviar Moneda", command=self.send_coin).grid(row=4, column=0, columnspan=2)

        self.address_list = tk.Text(master, height=10, width=50)
        self.address_list.grid(row=5, column=0, columnspan=2)

        self.tx_frame = tk.Frame(master)
        self.tx_frame.grid(row=6, column=0, columnspan=2)
        tk.Label(self.tx_frame, text="Destino").grid(row=0, column=0)
        self.dest_entry = tk.Entry(self.tx_frame)
        self.dest_entry.grid(row=0, column=1)
        tk.Label(self.tx_frame, text="Monto").grid(row=1, column=0)
        self.amount_entry = tk.Entry(self.tx_frame)
        self.amount_entry.grid(row=1, column=1)

    def create_wallet(self):
        name = self.name_entry.get()
        password = self.pass_entry.get()
        if not name or not password:
            messagebox.showerror("Error", "Ingrese nombre y contraseña")
            return
        wallet = SecureWallet(name)
        wallet.create_wallet(password)
        wallets[name] = wallet
        self.wallet = wallet
        messagebox.showinfo("Éxito", f"Wallet '{name}' creada!")

    def generate_address(self):
        if not self.wallet:
            messagebox.showerror("Error", "Primero cree una wallet")
            return
        addr = self.wallet.generate_address()
        blockchain.address_to_vk[addr] = self.wallet.private_key.get_verifying_key()
        self.address_list.insert(tk.END, f"{addr}\n")

    def send_coin(self):
        if not self.wallet:
            messagebox.showerror("Error", "Primero cree una wallet")
            return
        dest = self.dest_entry.get()
        amount = float(self.amount_entry.get())
        addr = self.wallet.public_keys[-1]
        signature = self.wallet.sign_message(f"{addr}{dest}{amount}")
        success = blockchain.add_transaction(addr, dest, amount, signature)
        if success:
            blockchain.mine_block()
            messagebox.showinfo("Éxito", f"Transacción enviada y bloque minado!\nSaldo actual: {blockchain.get_balance(addr)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WalletApp(root)
    root.mainloop()
