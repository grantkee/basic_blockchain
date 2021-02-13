import hashlib
import json
import requests
from textwrap import dedent
from time import time
from uuid import uuid4
from urllib.parse import urlparse

from flask import Flask, jsonify, request

class Blockchain(object):
  def __init__(self):
    self.current_transactions = []
    self.chain = []
    self.nodes = set()

    # create genesis block
    self.new_block(previous_hash = 1, proof = 100)

  def register_node(self, address):
    """
    Add a new node to the list of nodes
    :param address: <str> Address of node: ip/uri
    :return: None
    """

    parse_uri = urlparse(address)
    self.nodes.add(parse_uri.netloc)

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

  def proof_of_work(self, last_proof):
    """
      proof of work algorithm - simple version:
        - find a number p such that hash(pp') containst leading 4 zeroes, where p is the previous p'
        - p is the previous proof, and p' is the new proof
      :param last_proof: <int>
      :return: <int>
    """

    proof = 0
    while self.validate_proof(last_proof, proof) is False:
      proof += 1
    
    return proof

  def valid_chain(self, chain):
    """
    Determine if a given blockchain is valid
    :param chain: <list> given blockchain
    :return: <bool> True if valid, otherwise False
    """

    last_block = chain[0]
    current_index = 1

    while current_index < len(chain):
      block = chain[current_index]
      print(f'{last_block}')
      print(f'{block}')
      print("\n~~~~~~~~~~~~~\n")
      if block['previous_hash'] != self.hash(last_block):
        return False

      # verify proof of work
      if not self.validate_proof(last_block['proof'], block['proof']):
        return False

      last_block = block
      current_index += 1

    return True

  def resolve_conflicts(self):
    """
      Consensus algorithm: resolve conflicts by replacing our chain with the longest one in the network
      :return: <bool> True if the chain was replaced, otherwise False
    """

    community = self.nodes
    new_chain = None

    # compare length of chains to find the largest one
    max_length = len(self.chain)

    # fetch and verify all nodes in our network for node in community
    for node in community:
      response = requests.get(f'http://{node}/chain')

      if response.status_code == 200:
        length = response.json()['length']
        chain = response.json()['chain']

        # compare chain lengths to find the longest and therefore, valid chain
        if length > max_length and self.valid_chain(chain):
          max_length = length
          new_chain = chain

        # replace our chain if there is a valid, newer chain (longer than current)
        if new_chain:
          self.chain = new_chain
          return True

        return False

  @staticmethod
  def validate_proof(last_proof, proof):
    """
      checks if hash(last_proof, proof) contain 4 leading zeroes
      :param last_proof: <int> previous proof
      :param proof: <int> current proof
      :return: <bool> True if validated, else false
    """
    guess = f'{last_proof}{proof}'.encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:4] == "0000"

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

# instantiate the node
app = Flask(__name__)

#generate universally unique address for the node
node_identifier = str(uuid4()).replace('-', '')

# instantiate the blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
  # run the proof of work algorithm to get the next proof of work
  last_block = blockchain.last_block
  last_proof = last_block['proof']
  proof = blockchain.proof_of_work(last_proof)

  # reward mining effort after finding proof
  # sender is "0" to signify that this node has mined a new coin
  blockchain.new_transaction(
    sender = "0",
    recipient = node_identifier,
    amount = 1,
  )

  # forge the new Block by adding it to the chain
  previous_hash = blockchain.hash(last_block)
  block = blockchain.new_block(proof, previous_hash)

  response = {
    'message': "New Block Forged",
    'index': block['index'],
    'transactions': block['transactions'],
    'proof': block['proof'],
    'previous_hash': block['previous_hash']
  }

  return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
  values = request.get_json()
  # check that the required fields are in the POSTed data
  required = ['sender', 'recipient', 'amount']
  if not all(k in values for k in required):
    return 'missing values', 400
  
  # create new transaction
  index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

  response = {'message': f'transaction added to Block {index}'}
  return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
  response = {
    'chain': blockchain.chain,
    'length': len(blockchain.chain)
  }
  return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
  values = request.get_json()

  nodes = values.get('nodes')
  if nodes is None:
    return "error: invalid list of nodes", 400

  for node in nodes:
    blockchain.register_node(node)

    response = {
      'message': 'new nodes added',
      'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
  replaced = blockchain.resolve_conflicts()

  if replaced:
    response = {
      'message': 'blockchain updated',
      'chain': blockchain.chain
    }
  else:
    response = {
      'message': 'current blockchain up-to-date',
      'chain': blockchain.chain
    }
  
  return jsonify(response), 200
  
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=4000)
