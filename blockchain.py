import hashlib
import json
from time import time

class Blockchain(object):
  def __init__(self):
    self.current_transactions = []
    self.chain = []

    # create genesis block
    self.new_block(previous_hash = 1, proof = 100)

  def new_block(self, proof, previous_hash = None):
    """
      Create a new Block in the Blockchain
      :param proof: <int> return from Proof of Work algorithm
      :param previous_hash: (optional) <str> hash from previous block in chain - 1st block has none
      :return: <dict> the new block
    """
    block = {
      'index': len(self.chain) + 1,
      'timestamp': time(),
      'transactions': self.current_transactions,
      'proof': proof,
      'previous_hash': previous_hash or self.hash(self.chain[-1]),
    }

    # reset current list of transactions
    self.current_transactions = []

    self.chain.append(block)
    return block
  
  def new_transaction(self, sender, recipient, amount):
    """
    creates a new transaction to go into the next mined Block
    :param sender: <str> address of the sender
    :param recipient: <str> address of recipient
    :param amount: <int> amount to send
    :return: <int> the index of the Block that holds the transaction
    """

    self.current_transactions.append({
      'sender': sender,
      'recipient': recipient,
      'amount': amount,
    })

    return self.last_block['index'] + 1

  @staticmethod
  def hash(block):
    # hashes a Block
    """
      hash the block using SHA-256
      :param block: <dict> Block
      :return: <str> hashed string
    """
    # dictionary must be ordered for consistent hashes
    block_string = json.dumps(block, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()

  @property
  def last_block(self):
    # returns the last Block in the chain
    return self.chain[-1]
