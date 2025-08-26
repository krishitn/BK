"""
Simple Blockchain Money Transaction (Python)
File: blockchain_money_transaction.py

This is a self-contained, educational blockchain implementation with:
- Wallets using ECDSA key pairs
- Signed transactions
- Proof-of-Work mining
- Simple in-memory ledger and balance calculation

Dependencies:
- ecdsa  (install with: pip install ecdsa)

How to run:
1. pip install ecdsa
2. python3 blockchain_money_transaction.py

How to put on GitHub (quick steps):
1. git init
2. git add blockchain_money_transaction.py
3. git commit -m "Add simple blockchain money transaction demo"
4. Create a new repository on GitHub (via website) and follow the remote add/push commands GitHub gives you, e.g.:
   git remote add origin https://github.com/<username>/<repo>.git
   git branch -M main
   git push -u origin main

Note: This implementation is for learning and demonstration purposes only. Do NOT use this in production.
"""

import time
import json
import hashlib
import binascii
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from typing import List


class Wallet:
    """Create a wallet with ECDSA secp256k1 keypair."""
    def __init__(self):
        self._signing_key = SigningKey.generate(curve=SECP256k1)
        self._verifying_key = self._signing_key.get_verifying_key()

    @property
    def private_key(self) -> str:
        return binascii.hexlify(self._signing_key.to_string()).decode()

    @property
    def public_key(self) -> str:
        return binascii.hexlify(self._verifying_key.to_string()).decode()

    def sign(self, message: str) -> str:
        """Sign a UTF-8 message (string) and return signature hex."""
        sig = self._signing_key.sign(message.encode())
        return binascii.hexlify(sig).decode()

    def export_keys(self) -> dict:
        return {"private_key": self.private_key, "public_key": self.public_key}


class Transaction:
    """A transaction: sender_pub -> recipient_pub : amount with signature."""
    def __init__(self, sender_pub: str, recipient_pub: str, amount: float, signature: str = None):
        self.sender_pub = sender_pub
        self.recipient_pub = recipient_pub
        self.amount = amount
        self.signature = signature
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "sender_pub": self.sender_pub,
            "recipient_pub": self.recipient_pub,
            "amount": self.amount,
            "timestamp": self.timestamp,
        }

    def sign_transaction(self, signing_key_hex: str):
        """Sign using a hex private key (must match sender_pub)."""
        sk = SigningKey.from_string(binascii.unhexlify(signing_key_hex), curve=SECP256k1)
        message = json.dumps(self.to_dict(), sort_keys=True)
        sig = sk.sign(message.encode())
        self.signature = binascii.hexlify(sig).decode()

    def is_valid(self) -> bool:
        # If it's a mining reward, sender_pub is set to 'SYSTEM' and no signature needed
        if self.sender_pub == 'SYSTEM':
            return True
        if not self.signature:
            return False
        try:
            vk = VerifyingKey.from_string(binascii.unhexlify(self.sender_pub), curve=SECP256k1)
            message = json.dumps(self.to_dict(), sort_keys=True).encode()
            vk.verify(binascii.unhexlify(self.signature), message)
            return True
        except (BadSignatureError, Exception):
            return False


class Block:
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str = ''):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [t.to_dict() | {"signature": t.signature} for t in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine(self, difficulty: int):
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()


class Blockchain:
    def __init__(self, difficulty: int = 3, mining_reward: float = 50.0):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.pending_transactions: List[Transaction] = []
        self.mining_reward = mining_reward
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, [], '0')
        genesis.hash = genesis.calculate_hash()
        self.chain.append(genesis)

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction) -> bool:
        if not transaction.sender_pub or not transaction.recipient_pub:
            raise ValueError('Transaction must include sender and recipient public keys')
        if not transaction.is_valid():
            print('Invalid transaction signature. Rejecting transaction.')
            return False
        # Optional: check sender balance to prevent overspend
        sender_balance = self.get_balance_of_address(transaction.sender_pub)
        if transaction.sender_pub != 'SYSTEM' and sender_balance < transaction.amount:
            print('Sender has insufficient balance. Rejecting transaction.')
            return False
        self.pending_transactions.append(transaction)
        return True

    def mine_pending_transactions(self, miner_address: str):
        # Reward transaction (from SYSTEM)
        reward_tx = Transaction('SYSTEM', miner_address, self.mining_reward)
        self.pending_transactions.append(reward_tx)

        block = Block(len(self.chain), list(self.pending_transactions), self.get_latest_block().hash)
        print(f'Mining block {block.index} with {len(block.transactions)} transactions...')
        block.mine(self.difficulty)
        print(f'Block mined: {block.hash}')

        self.chain.append(block)
        self.pending_transactions = []

    def get_balance_of_address(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender_pub == address:
                    balance -= tx.amount
                if tx.recipient_pub == address:
                    balance += tx.amount
        # pending txs also considered (optional)
        for tx in self.pending_transactions:
            if tx.sender_pub == address:
                balance -= tx.amount
            if tx.recipient_pub == address:
                balance += tx.amount
        return balance

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                print('Invalid block hash at index', i)
                return False
            if current.previous_hash != previous.hash:
                print('Invalid chain linkage at index', i)
                return False
            # validate transactions in block
            for tx in current.transactions:
                if not tx.is_valid():
                    print('Invalid transaction in block', i)
                    return False
        return True


# ---------------------- Demo / Usage ----------------------
if __name__ == '__main__':
    print('\n=== Simple Blockchain Money Transaction Demo ===\n')

    # Create a blockchain
    demo_chain = Blockchain(difficulty=3, mining_reward=100.0)

    # Create wallets
    alice = Wallet()
    bob = Wallet()
    miner = Wallet()

    print('Alice public key (short):', alice.public_key[:40], '...')
    print('Bob public key (short):', bob.public_key[:40], '...')
    print('Miner public key (short):', miner.public_key[:40], '...')

    # Create a transaction: Alice -> Bob : 10
    tx1 = Transaction(alice.public_key, bob.public_key, 10.0)
    tx1.sign_transaction(alice.private_key)
    added = demo_chain.add_transaction(tx1)
    print('Transaction added to pool?', added)

    # Mine pending transactions by miner
    demo_chain.mine_pending_transactions(miner.public_key)

    print('\nBalances after 1st mining:')
    print('Alice:', demo_chain.get_balance_of_address(alice.public_key))
    print('Bob:', demo_chain.get_balance_of_address(bob.public_key))
    print('Miner:', demo_chain.get_balance_of_address(miner.public_key))

    # Create more transactions
    tx2 = Transaction(bob.public_key, alice.public_key, 4.5)
    tx2.sign_transaction(bob.private_key)
    demo_chain.add_transaction(tx2)

    # Mine again
    demo_chain.mine_pending_transactions(miner.public_key)

    print('\nBalances after 2nd mining:')
    print('Alice:', demo_chain.get_balance_of_address(alice.public_key))
    print('Bob:', demo_chain.get_balance_of_address(bob.public_key))
    print('Miner:', demo_chain.get_balance_of_address(miner.public_key))

    # Chain validity check
    print('\nIs chain valid?', demo_chain.is_chain_valid())

    print('\nYou can export the keys printed above to reuse wallets in future runs.\n')

