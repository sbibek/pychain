import hashlib as hasher
import datetime as date
import random
import copy

class Block:
  def __init__(self, index, timestamp, transactions, previous_hash, nonce):
    self.index = index
    self.timestamp = timestamp
    self.transactions = transactions
    self.nonce = nonce
    self.previous_hash = previous_hash
    self.hash = self.hashBlock()

  def hashBlock(self):
    sha = hasher.sha256()
    sha.update(
      str(self.timestamp).encode('utf-8') +
      str(self.transactions).encode('utf-8') + # to be replaced by merkle root 
      str(self.nonce).encode('utf-8') +
      str(self.previous_hash).encode('utf-8')
    )
    return sha.hexdigest()
  

class Blockchain:
  def __init__(self):
    self.blocks = []
    self.currentblock = Block(0, date.datetime.now(),[], "0", 0) 

  def addTransactions(self, transaction):
    verdict = self.validateTransaction(transaction)
    if verdict:
      self.currentblock.transactions.append(transaction)
    return verdict

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

  def lastBlock(self):
    return self.blocks[-1]

  def commitBlock(self, block):
    blk = Block(block.index, block.timestamp, block.transactions, block.previous_hash, block.nonce)
    blk.hash = block.hash
    self.blocks.append(blk)
    self.currentblock = Block(0, date.datetime.now(),[], "0", 0) 


class Miner:
  def __init__(self, name, cpu=1):
    self.name = name
    self.cpu = cpu
    self.blockchain = Blockchain()
  
  def log(self):
    print("\n******** {} ********".format(self.name))
    i = 0
    for block in self.blockchain.blocks:
      print(" <{}> nonce: {} transactions: {}".format(i, block.nonce, str(block.transactions)))
      print(" <{}> prev_hash: {} hash: {}".format(i, block.previous_hash, block.hash))
      i += 1

  def addTransaction(self, transaction):
    return self.blockchain.addTransactions(copy.deepcopy(transaction))
  
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

  def updateCurrentBlock(self, nonce, hash):
    self.blockchain.currentblock
  
  def validateBlock(self, block, hashDifficult):
    return int(block.hashBlock(),16) < hashDifficult and self.blockchain.lastBlock().hash == block.previous_hash

  def commitBlock(self, block):
    self.blockchain.commitBlock(block)



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

  def mineBlock(self, block):
    m = block.hashBlock()
    while int(m, 16) >= self.difficulty_hash:
      block.nonce += 1
      m = block.hashBlock()
    block.hash = m
    return m 

  def broadcastMinedBlock(self, block):
    for miner in self.uniqueMiners:
      if miner.validateBlock(block, self.difficulty_hash):
        miner.commitBlock(block)
      else:
        print("miner {} was not able to validate the block".format(miner.name))
  
  def log(self):
    # invoke logging of chain for all miners
    for miner in self.uniqueMiners:
      miner.log()


  def simulate(self):
    index = 0
    genesisBlock = Block(index, date.datetime.now(),{}, "0", 0)
    previoushash = genesisBlock.hashBlock()
    predefinedblocks = []
    predefinedblocks.append(genesisBlock)
    # for the first predefined conditions, we just run PoW and set them to all the miners
    for t in self.predefinedTransactions:
      block = Block(index+1, date.datetime.now(),[t], previoushash,0)
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
      for miner in self.uniqueMiners:
       verdict &= miner.addTransaction(copy.deepcopy(transaction))
      
      # if transactions was not verified, then discard the transaction
      if verdict == False:
        continue

      # else means the transaction was added then we now can run mine race between the miners
      nonce = 0 
      success = False
      while success == False:
        for miner in self.miners:
          success, currblock = miner.tryNextMining(index, nonce, self.difficulty_hash)
          if not success:
            nonce = nonce + 1
            continue

          # if we are here means that the mining was successful, 
          # let all the miners check if they think this is valid one
          print("Transaction = {} Miner <{}> mined the block, nonce = {}".format(str(transaction), miner.name, nonce))

          # send updates to all the miners
          self.broadcastMinedBlock(currblock)
          break


miner1 = Miner("Debra", cpu=1)
miner2 = Miner("Akin", cpu=2)
miner3 = Miner("Nagmat", cpu=3)

# considering predefined transactions where grahm has provided
# all the other uses initial fund of 100
predefinedTransactions = [
  {'from': 'grahm', 'to': 'alice', 'amount': 100},
  {'from': 'grahm', 'to': 'bob', 'amount': 100 },
  {'from': 'grahm', 'to': 'charlie', 'amount': 100 }
]

simulatedTransactions = [
  {'from': 'alice', 'to': 'bob', 'amount': 10},
  {'from': 'alice', 'to': 'charlie', 'amount': 50},
  {'from': 'bob', 'to': 'charlie', 'amount': 30},
]

simulation = Simulation(miners=[miner1, miner2, miner3], predefinedTransactions=predefinedTransactions, simulatedTransactions = simulatedTransactions)
simulation.simulate()
simulation.log()
