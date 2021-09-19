import hashlib as hasher
import datetime as date
import random
import copy

class MerkleTree:
  def getTree(self, transactions):
    if len(transactions) % 2 != 0:
      transactions.append({})

    tree = []
    
    leaves = []
    for t in transactions:
      leaves.append(self.__getHash(t))  
    tree.append(leaves)

    self.__genTree(transactions, tree)
    return list(reversed(tree))

  def __genTree(self, transactions, result):
    tns = []
    for i in range(0, len(transactions), 2):
      tns.append(self.__getHash(str(transactions[i])+str(transactions[i+1])))
    
    result.append(tns)
    if len(tns) > 1:
      self.__genTree(tns, result)


  def __getHash(self, transaction):
    sha = hasher.sha256()
    sha.update(str(transaction).encode('utf-8'))
    return sha.hexdigest()

class Block:
  def __init__(self, index, timestamp, transactions, previous_hash, nonce):
    self.index = index
    self.timestamp = timestamp
    self.transactions = transactions
    self.merkletree = []
    self.nonce = nonce
    self.previous_hash = previous_hash
    self.hash = self.hashBlock()

  def hashBlock(self):
    sha = hasher.sha256()
    sha.update(
      str(self.timestamp).encode('utf-8') +
      str(self.transactions).encode('utf-8') + # to be replaced by merkle root 
      str(self.merkletree[0][0] if len(self.merkletree) > 0 else "").encode('utf-8') +
      str(self.nonce).encode('utf-8') +
      str(self.previous_hash).encode('utf-8')
    )
    return sha.hexdigest()
  

class Blockchain:
  def __init__(self):
    self.blocks = []
    self.currentblock = Block(0, date.datetime.now(),[], "0", 0) 
    self.merklefn = MerkleTree()

  def addTransactions(self, transaction):
    verdict = self.validateTransaction(transaction)
    if verdict:
      self.currentblock.transactions.append(transaction)
      self.currentblock.merkletree = self.merklefn.getTree(copy.deepcopy(self.currentblock.transactions))
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
    blk = copy.deepcopy(block) 
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
      print(" <{}> root of merkle tree : {}".format(i, str(block.merkletree[0][0]) if len(block.merkletree) > 0 else ""))
      print(" <{}> prev_hash: {} hash: {}".format(i, block.previous_hash, block.hash))
      print()
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
    bhash = int(block.hashBlock(),16) 
    return bhash < hashDifficult and self.blockchain.lastBlock().hash == block.previous_hash

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
        print("  Miner <{}> says the block is valid".format(miner.name))
        miner.commitBlock(block)
      else:
        print("  Miner <{}> was not able to validate the block".format(miner.name))
  
  def log(self):
    # invoke logging of chain for all miners
    for miner in self.uniqueMiners:
      miner.log()


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
  {'from': 'charlie', 'to': 'bob', 'amount': 76},
  {'from': 'bob', 'to': 'alice', 'amount': 20},
  {'from': 'charlie', 'to': 'alice', 'amount': 30},
]

simulation = Simulation(miners=[miner1, miner2, miner3], predefinedTransactions=predefinedTransactions, simulatedTransactions = simulatedTransactions)
simulation.simulate()
simulation.log()
