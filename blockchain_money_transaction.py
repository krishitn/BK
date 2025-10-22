import hashlib
import time
import tkinter as tk
from tkinter import ttk, messagebox


# =======================
# Utility Functions
# =======================
def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def now() -> int:
    return int(time.time())


# =======================
# Transaction Class
# =======================
class Transaction:
    def __init__(self, sender: str, receiver: str, amount: float):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def __repr__(self):
        return f"{self.sender} -> {self.receiver}: ₹{self.amount}"


# =======================
# Block Class
# =======================
class Block:
    def __init__(self, index: int, transactions: list, prev_hash: str, difficulty: int = 3):
        self.index = index
        self.transactions = transactions
        self.timestamp = now()
        self.prev_hash = prev_hash
        self.nonce = 0
        self.difficulty = difficulty
        self.hash = self.mine_block()

    def compute_hash(self) -> str:
        tx_str = "".join(str(tx) for tx in self.transactions)
        data = f"{self.index}{self.timestamp}{self.prev_hash}{tx_str}{self.nonce}"
        return sha256(data)

    def mine_block(self) -> str:
        prefix = "0" * self.difficulty
        while True:
            h = self.compute_hash()
            if h.startswith(prefix):
                return h
            self.nonce += 1


# =======================
# Blockchain Class
# =======================
class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_txs = []
        self.difficulty = 3
        self.balances = {"BANK": 1_000_000.0}

    def create_genesis_block(self) -> Block:
        return Block(0, ["Genesis Block"], "0")

    def get_balance(self, user: str) -> float:
        return self.balances.get(user, 0.0)

    def update_balances(self, txs):
        for tx in txs:
            if isinstance(tx, Transaction):
                self.balances[tx.sender] = self.balances.get(tx.sender, 0.0) - tx.amount
                self.balances[tx.receiver] = self.balances.get(tx.receiver, 0.0) + tx.amount

    def add_transaction(self, tx: Transaction):
        if tx.sender != "BANK" and self.get_balance(tx.sender) < tx.amount:
            return False
        self.pending_txs.append(tx)
        return True

    def mine_pending_txs(self):
        if not self.pending_txs:
            return None

        prev_hash = self.chain[-1].hash
        new_block = Block(len(self.chain), self.pending_txs, prev_hash, self.difficulty)
        self.chain.append(new_block)
        self.update_balances(self.pending_txs)
        self.pending_txs = []
        return new_block


# =======================
# GUI Application
# =======================
class BlockchainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏦 Bank Blockchain GUI")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        self.chain = Blockchain()

        self.setup_ui()

    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="🏦 BankChain - Blockchain Banking System",
                         font=("Arial", 18, "bold"))
        title.pack(pady=10)

        # Transaction frame
        frame = ttk.LabelFrame(self.root, text="New Transaction", padding=10)
        frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(frame, text="Sender:").grid(row=0, column=0, padx=5, pady=5)
        self.sender_entry = ttk.Entry(frame, width=20)
        self.sender_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Receiver:").grid(row=0, column=2, padx=5, pady=5)
        self.receiver_entry = ttk.Entry(frame, width=20)
        self.receiver_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Amount (₹):").grid(row=0, column=4, padx=5, pady=5)
        self.amount_entry = ttk.Entry(frame, width=10)
        self.amount_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(frame, text="Add Transaction", command=self.add_transaction).grid(row=0, column=6, padx=10)

        # Action buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Mine Block", command=self.mine_block).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Show Balances", command=self.show_balances).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="Show Blockchain", command=self.show_chain).grid(row=0, column=2, padx=10)

        # Output area
        self.output = tk.Text(self.root, height=20, width=95, wrap="word", font=("Courier", 10))
        self.output.pack(padx=10, pady=10)

        self.log("System ready. BANK starts with ₹1,000,000 reserve.\n")

    # ==========================
    # Blockchain GUI Functions
    # ==========================
    def log(self, message: str):
        self.output.insert(tk.END, message + "\n")
        self.output.see(tk.END)

    def add_transaction(self):
        sender = self.sender_entry.get().strip()
        receiver = self.receiver_entry.get().strip()
        try:
            amount = float(self.amount_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
            return

        if not sender or not receiver:
            messagebox.showerror("Error", "Sender and Receiver are required.")
            return

        tx = Transaction(sender, receiver, amount)
        if self.chain.add_transaction(tx):
            self.log(f"🧾 Added: {tx}")
            self.sender_entry.delete(0, tk.END)
            self.receiver_entry.delete(0, tk.END)
            self.amount_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Insufficient Funds", f"{sender} has insufficient balance.")

    def mine_block(self):
        if not self.chain.pending_txs:
            messagebox.showinfo("Mining", "No transactions to mine.")
            return

        self.log("\n⛏️ Mining new block, please wait...")
        self.root.update()

        block = self.chain.mine_pending_txs()
        if block:
            self.log(f"✅ Block {block.index} mined! Hash: {block.hash[:16]}...\n")
        else:
            messagebox.showinfo("Mining", "No block mined.")

    def show_balances(self):
        balances = "\n💰 Account Balances:\n"
        for user, bal in sorted(self.chain.balances.items()):
            balances += f"  {user}: ₹{bal}\n"
        self.log(balances)

    def show_chain(self):
        text = "\n📜 Blockchain Ledger:\n"
        for block in self.chain.chain:
            text += f"\nBlock {block.index} | Time: {time.ctime(block.timestamp)}\n"
            text += f"Prev Hash: {block.prev_hash[:15]}...\n"
            text += f"Hash: {block.hash[:15]}...\n"
            text += "Transactions:\n"
            for tx in block.transactions:
                text += f"  - {tx}\n"
        self.log(text)


# =======================
# Entry Point
# =======================
if __name__ == "__main__":
    root = tk.Tk()
    app = BlockchainApp(root)
    root.mainloop()
