import hashlib as hasher
import datetime as date
import random
import copy

# Simple MerkleTree Implementation 
# This class takes in leaves which are transactions of the block lets say T  
# It uses sha256 to hash all the transactions in T and then incrementally
# combine two hashes to form single parent hash until we get last one hash which is merkle root
# Array of hashes are returned where first hash is the root
class MerkleTree:

  # Returns merkle tree for given transactions
  def getTree(self, transactions):
    # if there is odd number of transactions, we add one dummy one to make it even
    if len(transactions) % 2 != 0:
      transactions.append({})
    tree = []
    leaves = []
    # get hash of the leaves
    for t in transactions:
      leaves.append(self.__getHash(t))  
    tree.append(leaves)

    # create incremental parent hashes until root is reached
    self.__genTree(transactions, tree)
    return list(reversed(tree))

  # Recursive function to calculate parent root until root
  def __genTree(self, transactions, result):
    tns = []
    for i in range(0, len(transactions), 2):
      tns.append(self.__getHash(str(transactions[i])+str(transactions[i+1])))
    
    result.append(tns)
    if len(tns) > 1:
      self.__genTree(tns, result)

  # use sha256 for merkle tree
  def __getHash(self, transaction):
    sha = hasher.sha256()
    sha.update(str(transaction).encode('utf-8'))
    return sha.hexdigest()


# Block of the Blockchain 
# Holds the transactions, timestamp, merkletree, nonce, 
# previous and current hashes
#
class Block:
  def __init__(self, index, timestamp, transactions, previous_hash, nonce):
    self.index = index
    self.timestamp = timestamp
    self.transactions = transactions
    self.merkletree = []
    self.nonce = nonce
    self.previous_hash = previous_hash
    self.hash = self.hashBlock()

  # Converts the block parameters to string and then calculates the hash
  # using sha256
  def hashBlock(self):
    sha = hasher.sha256()
    sha.update(
      str(self.timestamp).encode('utf-8') +
      str(self.transactions).encode('utf-8') + 
      str(self.merkletree[0][0] if len(self.merkletree) > 0 else "").encode('utf-8') +
      str(self.nonce).encode('utf-8') +
      str(self.previous_hash).encode('utf-8')
    )
    return sha.hexdigest()
  

# Blockchain holds all the mined blocks and also the current block
# current block holds the transactions and is added to the blocks
# after it is mined
class Blockchain:
  def __init__(self):
    self.blocks = []
    self.currentblock = Block(0, date.datetime.now(),[], "0", 0) 
    self.merklefn = MerkleTree()

  # adding transaction would first make sure that the transaction is valid
  # merkle tree is also calculated and added to the block if its valid
  # finally transaction is added to current block if it is validated
  def addTransactions(self, transaction):
    verdict = self.validateTransaction(transaction)
    if verdict:
      self.currentblock.transactions.append(transaction)
      self.currentblock.merkletree = self.merklefn.getTree(copy.deepcopy(self.currentblock.transactions))
    return verdict

  # Utility function to validate transaction
  # A transaction is valid is the user transferring the amount has sufficient funds to do so
  def validateTransaction(self, transaction):
    fromUser = transaction['from']
    # now we will check if this user has enough fund to do this transaction
    # we can just skip the first miner
    availableFunds = 0
    for block in self.blocks[1:]:
      for tran in block.transactions:
        if(tran['to'] == fromUser):
          # means this user received some funds
          availableFunds += tran['amount']
        
        if(tran['from'] == fromUser):
          # means this user spent some funds
          availableFunds -= tran['amount']
    # the transaction is validated only and only if the amount 
    # being spend is something the user has
    return availableFunds >= transaction['amount']

  # Utility function to get last block
  def lastBlock(self):
    return self.blocks[-1]

  # Adds the current block to the blockchain
  def commitBlock(self, block):
    blk = copy.deepcopy(block) 
    blk.hash = block.hash
    self.blocks.append(blk)
    self.currentblock = Block(0, date.datetime.now(),[], "0", 0) 


# Miner is depection of individual miners 
# Each miner is given a name and the amount of cpus it has 
# which shows how much mining power it has
class Miner:
  def __init__(self, name, cpu=1):
    self.name = name
    self.cpu = cpu
    self.blockchain = Blockchain()

  # log the current state of blockchain in the current miner 
  def log(self):
    print("\n******** {} ********".format(self.name))
    i = 0
    for block in self.blockchain.blocks:
      print(" <{}> timestamp:{}".format(i, block.timestamp))
      print(" <{}> nonce: {} transactions: {}".format(i, block.nonce, str(block.transactions)))
      print(" <{}> root of merkle tree : {}".format(i, str(block.merkletree[0][0]) if len(block.merkletree) > 0 else ""))
      print(" <{}> prev_hash: {} hash: {}".format(i, block.previous_hash, block.hash))
      print()
      i += 1

  # Add transaction to the blockchain of this miner
  def addTransaction(self, transaction):
    return self.blockchain.addTransactions(copy.deepcopy(transaction))

  # Mine the current block
  # Since this is just simulation, so we instead of running each miner individually, we will run the one by one
  # providing previous failed nonce +1 for trying to mine until hashDifficulty is satisfied
  def tryNextMining(self, index, currentNonce, hashDifficulty):
    # lets update the previous hash and index
    self.blockchain.currentblock.index = index
    self.blockchain.currentblock.previous_hash = self.blockchain.lastBlock().hash
    block = self.blockchain.currentblock
    block.nonce = currentNonce
    m = block.hashBlock()
    verdict = int(m, 16) < hashDifficulty
    if verdict: 
      # update the hash
      block.hash = m
    return verdict, block

  # Validate block to check if the nonce is correct and the previous hash is correct too
  def validateBlock(self, block, hashDifficult):
    bhash = int(block.hashBlock(),16) 
    return bhash < hashDifficult and self.blockchain.lastBlock().hash == block.previous_hash

  # commit the current block to the blockchain of this miner
  def commitBlock(self, block):
    self.blockchain.commitBlock(block)


# Simulate the blockchain with multiple miners
# We assume that there is pre-existing transactions which be mined for all blocks
# before simulation starts
class Simulation:
  def __init__(self, miners, predefinedTransactions=[], simulatedTransactions=[]):
    # set difficulty for the proof of work
    self.difficulty_hash = 0x00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    self.uniqueMiners = miners
    # now create all the miner instances according to their CPU
    self.miners = []
    for _m in [m.cpu * [m] for m in miners]:
      self.miners.extend(_m)
    random.shuffle(self.miners)

    self.predefinedTransactions = predefinedTransactions
    self.sumulatedTransactions = simulatedTransactions

  # miner for pre-exsting transactions, block
  def mineBlock(self, block):
    m = block.hashBlock()
    while int(m, 16) >= self.difficulty_hash:
      block.nonce += 1
      m = block.hashBlock()
    block.hash = m
    return m 

  # broadcasts the mined block to all the miners
  def broadcastMinedBlock(self, block):
    for miner in self.uniqueMiners:
      if miner.validateBlock(block, self.difficulty_hash):
        print("  Miner <{}> says the block is valid".format(miner.name))
        miner.commitBlock(block)
      else:
        print("  Miner <{}> was not able to validate the block".format(miner.name))
  
  def log(self):
    # invoke logging of chain for all miners
    for miner in self.uniqueMiners:
      miner.log()

  # start the simulation
  # first create the genesis block
  # then mine all the pre-existing blocks
  # then simulate all the transactions
  def simulate(self):
    index = 0
    genesisBlock = Block(index, date.datetime.now(),{"Genesis": "Block"}, "0", 0)
    previoushash = genesisBlock.hashBlock()
    predefinedblocks = []
    predefinedblocks.append(genesisBlock)
    # for the first predefined conditions, we just run PoW and set them to all the miners

    mtree = MerkleTree()
    for t in self.predefinedTransactions:
      block = Block(index+1, date.datetime.now(),[t], previoushash,0)
      block.merkletree = mtree.getTree(copy.deepcopy([t])) 
      previoushash = self.mineBlock(block)
      predefinedblocks.append(block)
    
    # now lets share this initial ledger with all the miners
    for miner in self.miners:
      a = []
      for b in predefinedblocks:
        a.append(copy.deepcopy(b))
      miner.blockchain.blocks = a 
    
    # now from this on all the transactions are added systematically
    for transaction in self.sumulatedTransactions:
      verdict = True
      print("\nTransaction received {}".format(str(transaction)))
      for miner in self.uniqueMiners:
       verdict &= miner.addTransaction(copy.deepcopy(transaction))
      
      # if transactions was not verified, then discard the transaction
      if verdict == False:
        continue

      # else means the transaction was added then we now can run mine race between the miners
      nonce = 0 
      success = False
      print("Miners now competing to mine current block".format(index))
      while success == False:
        for miner in self.miners:
          success, currblock = miner.tryNextMining(index, nonce, self.difficulty_hash)
          if not success:
            nonce = nonce + 1
            continue

          # if we are here means that the mining was successful, 
          # let all the miners check if they think this is valid one
          print("Miner <{}> successfully mined the block, nonce = {}".format(miner.name, nonce))

          # send updates to all the miners
          self.broadcastMinedBlock(currblock)
          print("Miner <{}> added the block to the blockchain and sent it to all other miners".format(miner.name))
          break


# Miners for this simulation
miner1 = Miner("Arif", cpu=1)
miner2 = Miner("Akin", cpu=2)
miner3 = Miner("Nagmat", cpu=3)

# considering predefined transactions where grahm has provided
# all the other uses initial fund of 100
predefinedTransactions = [
  {'from': 'grahm', 'to': 'alice', 'amount': 100},
  {'from': 'grahm', 'to': 'bob', 'amount': 100 },
  {'from': 'grahm', 'to': 'charlie', 'amount': 100 }
]

# These transactions will be simulated
simulatedTransactions = [
  {'from': 'alice', 'to': 'bob', 'amount': 10},
  {'from': 'alice', 'to': 'charlie', 'amount': 50},
  {'from': 'bob', 'to': 'charlie', 'amount': 30},
  {'from': 'charlie', 'to': 'bob', 'amount': 76},
  {'from': 'bob', 'to': 'alice', 'amount': 20},
  {'from': 'charlie', 'to': 'alice', 'amount': 30},
]

# start the simulation
simulation = Simulation(miners=[miner1, miner2, miner3], predefinedTransactions=predefinedTransactions, simulatedTransactions = simulatedTransactions)
simulation.simulate()
simulation.log()
