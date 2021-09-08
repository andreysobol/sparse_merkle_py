from hashlib import sha256
from functools import reduce
from typing import Union

class SparseMerkleTree():

    def __init__(self) -> None:
        self.empty_element = b'\0'
        self.cache_empty_values = {}

    def setup_depth(self, depth: int) -> None:
        self.depth = depth
        self.max_elements = 2**depth

    def get_root(self) -> bytes:
        if 0 in self.lists[self.depth]:
            return self.lists[self.depth][0]
        else:
            return self.calculate_empty_leaf_hash(self.depth)

    def calculate_level(self, levels, iteration):
        prev_level = levels[iteration]
        size = len(prev_level) // 2
        iterator = range(0, size)
        params = zip([iteration] * size, iterator)
        levels = levels + [{}]
        return reduce(self.calculate_and_update_leaf, params, levels)

    def calculate_full_tree(self, elements, depth):
        hashed_elements = dict(zip(range(0, len(elements)), [self.calculate_hash(element) for element in elements]))
        return reduce(self.calculate_level, range(0, depth), [hashed_elements])

    def set_elements(self, elements) -> None:
        self.elements = elements
        self.lists = self.calculate_full_tree(self.elements, self.depth)

    def initialise_empty(self) -> None:
        #elements = [self.empty_element for _ in range(0, self.max_elements)]
        self.elements = {}
        self.lists = [{} for _ in range(0, self.depth + 1)]
        #self.set_elements(elements)

    def calculate_empty_leaf_hash(self, level):

        if level in self.cache_empty_values:
            return self.cache_empty_values[level]

        if level == 0:
            v = self.calculate_hash(self.empty_element)
        else:
            prev = self.calculate_empty_leaf_hash(level - 1)
            v = self.calculate_hash(prev + prev)

        self.cache_empty_values[level] = v
        return v

    def calculate_leaf(self, lists, level, i) -> Union[list, type(None)]:
        full_level = lists[level]

        i0 = 2*i
        i1 = 2*i+1

        v0_exist = i0 in full_level
        v1_exist = i1 in full_level

        if (not v0_exist) and (not v1_exist):
            return None

        if v0_exist:
            v0 = full_level[i0]
        else:
            v0 = self.calculate_empty_leaf_hash(level)

        if v1_exist:
            v1 = full_level[i1]
        else:
            v1 = self.calculate_empty_leaf_hash(level)

        return self.calculate_hash(v0 + v1)

    def calculate_and_update_leaf(self, lists, params) -> list:
        (level, i) = params
        leaf = self.calculate_leaf(lists, level, i)
        lists[level+1][i] = leaf
        return lists

    def modify_element(self, index: int, value: bytes) -> None:
        self.elements[index] = value
        hashed_element = self.calculate_hash(value)
        self.lists[0][index] = hashed_element
        levels = range(0, self.depth)
        indexs = [index // (2**power) for power in range(1, self.depth+1)]
        params = zip(levels, indexs)
        self.lists = reduce(self.calculate_and_update_leaf, params, self.lists)

    def add_element(self, index: int, value: bytes) -> None:
        if index not in self.elements:
            self.modify_element(index, value)
        else:
            raise Exception('Value exist')

    def remove_element(self, index: int) -> None:
        if index in self.elements:
            self.modify_element(index, self.empty_element)
        else:
            raise Exception("Value doesn't exist")


class Sha256SparseMerkleTree(SparseMerkleTree):

    def calculate_hash(self, preimage) -> bytes:
        return sha256(preimage).digest()


if __name__ == "__main__":
    spt = Sha256SparseMerkleTree()
    spt.setup_depth(10)
    spt.initialise_empty()
    spt.get_root()
    spt.add_element(0, b"1234")
    for item in spt.lists:
        print(item)
        print()
    
    print(spt.cache_empty_values)