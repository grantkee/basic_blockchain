class Blockchain(object):
  def __init__(self):
    self.current_transactions = []

  def new_block(self):
    # creates a new Block and adds it to the chain
    pass
  
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
    pass

  @property
  def last_block(self):
    # returns the last Block in the chain
    pass
