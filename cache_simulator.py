import sys
import numpy as np
import random as rd

# Começa uma classe para os atributos de entrada
class Attributes:
    def __init__(self, nsets, bsize, assoc, sub, flag, file):
        self.nsets = nsets
        self.bsize = bsize
        self.assoc = assoc
        self.sub = sub
        self.flag = flag
        self.file = file
        self.hits = 0
        self.counter = 0

    def addHits(self):
        self.hits += 1
    
    def addCounter(self):
        self.counter += 1

# Cria um objeto da classe Attributes com os atributos de entrada
att = Attributes(
    int(sys.argv[1]), 
    int(sys.argv[2]), 
    int(sys.argv[3]), 
    sys.argv[4], 
    int(sys.argv[5]), 
    sys.argv[6]
)

# Começa uma classe para os misses
class Misses:
    def __init__(self):
        self.compulsory = 0
        self.conflict = 0
        self.capacity = 0
        self.total = 0

    def addCompulsory(self):
        self.compulsory += 1
        self.total += 1

    def addConflict(self):
        self.conflict += 1
        self.total += 1

    def addCapacity(self):
        self.capacity += 1
        self.total += 1

# Cria um objeto da classe Misses
misses = Misses()

#cria uma lista duplamente encadeada, por causa dos blocos, pra armazenar os indices e os blocos
class Node:
    def __init__(self, index):
        self.index = index
        self.next = None
        self.prev = None

class Sub:
    def __init__(self):
        self.head = None
        self.tail = None

    def add(self, index):
        new_node = Node(index)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node

    def move(self, node):
        if node == self.tail:
            return
        if node == self.head:
            self.head = node.next
            self.head.prev = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
        node.next = None
        node.prev = self.tail
        self.tail.next = node
        self.tail = node

    def remove(self):
        if self.head is None:
            return None
        removed = self.head.index
        self.head = self.head.next
        if self.head is not None:
            self.head.prev = None
        else:
            self.tail = None
        return removed

    def get_node(self, index):
        current_node = self.head
        while current_node is not None:
            if current_node.index == index:
                return current_node
            current_node = current_node.next
        return None

def main():
    
    sub_cache = Sub()
    full = 0
    # Verifica se o número de argumentos está correto
    if (len(sys.argv) != 7):
        print("Usage: python cache_simulator.py <nsets> <bsize> <assoc> <sub> <flag> <tracefile>")
        return

    # Inicializa os vetores de valores e tags da cache com o tamanho da associatividade vezes o número de conjuntos
    cache_val = [[0] * att.assoc for _ in range(att.nsets)]
    cache_tag = [[0] * att.assoc for _ in range(att.nsets)]

    # Calcula o número de bits de offset, index e tag
    offset_bits = int(np.log2(att.bsize))
    index_bits = int(np.log2(att.nsets))
    tag_bits = 32 - offset_bits - index_bits

    # Abre o arquivo de entrada e lê os dados em formato big endian
    file = open(att.file, "rb")
    data = np.fromfile(file, dtype=">u2")

    # Checa toda a cache pra ver se esta cheia
    full = all(all(row) for row in cache_val)

    # Itera sobre os dados do arquivo de entrada
    for i in range(0, data.size):   

        # Se for um endereço de memória ímpar, é um dado, se não vai ser um 0, foi a forma que achei de funcionar hehe
        if i % 2 != 0:
            # Calcula o tag e o index do endereço de memória
            tag = data[i] >> (offset_bits + index_bits)
            index = (data[i] >> offset_bits) & ((1 << index_bits) - 1)

            # Vê onde vai ser colocado o dado na cache
            cache_val, cache_tag = cache_placement(index, tag, cache_val, cache_tag, sub_cache)
            att.addCounter()

def cache_placement(index, tag, cache_val, cache_tag, sub_cache):
    # Checa se toda a cache está cheia
    full = all(all(row) for row in cache_val)

    # Verifica se o bloco já está na cache
    flag = False
    for i in range(att.assoc):
        if cache_tag[index][i] == tag:
            flag = True
            break

    # Se o bloco já estiver na cache, é um hit
    if flag:
        att.addHits()
        # Se for LRU, move o bloco para o final da lista encadeada
        if att.sub == 'L':
            node = sub_cache.get_node(index)
            sub_cache.move(node)
    else:
        # Incrementa o contador de misses
        if full:
            misses.addCapacity()
        else:
            if any(cache_val[index]):
                misses.addConflict()
            else:
                misses.addCompulsory()

        # Se a cache estiver cheia, remove o bloco mais antigo
        if full:
            if att.sub == 'F' and sub_cache.head is not None:
                removed_index = sub_cache.remove()
            elif att.sub == 'L' and sub_cache.head is not None:
                node = sub_cache.get_node(index)
                sub_cache.move(node)
            # Random
            else:  
                removed_index = rd.randint(0, 10) % att.assoc
                cache_val[index][removed_index] = 1
                cache_tag[index][removed_index] = tag
                sub_cache.add(index)
        else:
            # Encontra o primeiro bloco vazio e insere nele
            for i in range(att.assoc):
                if cache_val[index][i] == 0:
                    cache_val[index][i] = 1
                    cache_tag[index][i] = tag
                    sub_cache.add(index)
                    break

    return cache_val, cache_tag

if __name__ == "__main__":
    main()

    if att.flag == 1:
        print(f"{att.counter} {att.hits/att.counter:.4f} {misses.total/att.counter:.4f} {misses.compulsory/misses.total:.2f} {misses.capacity/misses.total:.2f} {misses.conflict/misses.total:.2f}")
    else:
        print(f"Quantidade de acessos: {att.counter}\nTaxa de acertos: {att.hits/att.counter:.4f}\nTaxa de misses: {misses.total/att.counter:.4f}\nMisses compulsórios: {misses.compulsory/misses.total:.2f}\nMisses de capacidade: {misses.capacity/misses.total:.2f}\nMisses de conflito: {misses.conflict/misses.total:.2f}")