from hashlib import sha256
from functools import reduce
from typing import Union

class SparseMerkleTree():

    def __init__(self, depth: int) -> None:
        self._check_b_than_0(depth, "Depth")
        self.empty_element = b'\0'
        self.cache_empty_values = {}
        self._setup_depth(depth)
        self.elements = {}
        self.lists = [{} for _ in range(0, self.depth + 1)]

    @classmethod
    def _check_b_than_0(cls, depth: int, name: str):
        if depth < 1:
            raise ValueError(name + " should be > 0")

    def _setup_depth(self, depth: int) -> None:
        self.depth = depth
        self.max_elements = 2**depth

    def increase_depth(self, amount_of_level: int) -> None:
        self._check_b_than_0(amount_of_level, "amount_of_level")

        old_depth = self.depth
        new_depth = self.depth + amount_of_level

        params = zip(range(old_depth, new_depth), [0] * amount_of_level)
        lists = self.lists + [{} for _ in range(old_depth, new_depth)]
        self.lists = reduce(self._calculate_and_update_leaf, params, lists)

        self._setup_depth(new_depth)

    def decrease_depth(self, amount_of_level: int) -> None:
        old_depth = self.depth
        new_depth = self.depth - amount_of_level

        self._check_b_than_0(amount_of_level, "amount_of_level")
        self._check_b_than_0(new_depth, "Depth")

        levels_check = range(new_depth, old_depth)
        lists = self.lists
        if False in [False for l in levels_check if 1 in lists[l]]:
            raise IndexError('Trying to remove non empty subtree')

        self._setup_depth(new_depth)

    def get_root(self) -> bytes:
        if 0 in self.lists[self.depth]:
            return self.lists[self.depth][0]

        return self._calculate_empty_leaf_hash(self.depth)

    def _calculate_level(
        self,
        levels: list[dict[int, bytes]],
        iteration: int,
    ) -> list[dict[int, bytes]]:
        size = 2 ** (self.depth - iteration - 1)
        iterator = range(0, size)
        params = zip([iteration] * size, iterator)
        levels = levels + [{}]
        return reduce(self._calculate_and_update_leaf, params, levels)

    def _calculate_full_tree(
        self,
        elements: dict[int, bytes],
        depth: int,
    ) -> list[dict[int, bytes]]:
        hashed_elements = {
            k:self._calculate_hash(elements[k]) for k in elements
        }
        return reduce(self._calculate_level, range(0, depth), [hashed_elements])

    def set_elements(self, elements: list[bytes]) -> None:
        if self.max_elements < len(elements):
            raise IndexError("Too many elements")

        self.elements = {
            i:elements[i] for i in range(0, len(elements)) if elements[i] != self.empty_element
        }
        self.lists = self._calculate_full_tree(self.elements, self.depth)

    def _calculate_empty_leaf_hash(self, level: dict[int, bytes]) -> bytes:

        if level in self.cache_empty_values:
            return self.cache_empty_values[level]

        if level == 0:
            value = self._calculate_hash(self.empty_element)
        else:
            prev = self._calculate_empty_leaf_hash(level - 1)
            value = self._calculate_hash(prev + prev)

        self.cache_empty_values[level] = value
        return value

    def _calculate_leaf(
        self,
        lists:list[dict[int, bytes]],
        level:int,
        i: int,
    ) -> Union[list, type(None)]:

        full_level = lists[level]

        i_0 = 2*i
        i_1 = 2*i+1

        v0_exist = i_0 in full_level
        v1_exist = i_1 in full_level

        if (not v0_exist) and (not v1_exist):
            return None

        if v0_exist:
            v_0 = full_level[i_0]
        else:
            v_0 = self._calculate_empty_leaf_hash(level)

        if v1_exist:
            v_1 = full_level[i_1]
        else:
            v_1 = self._calculate_empty_leaf_hash(level)

        return self._calculate_hash(v_0 + v_1)

    def _calculate_and_update_leaf(
        self,
        lists: list[dict[int, bytes]],
        params: (int, int)
    ) -> list[dict[int, bytes]]:
        (level, i) = params
        leaf = self._calculate_leaf(lists, level, i)
        if leaf:
            lists[level+1][i] = leaf
        else:
            if i in lists[level+1]:
                del lists[level+1][i]
        return lists

    def modify_element(self, index: int, value: bytes) -> None:

        if index not in range(0, self.max_elements):
            raise IndexError('Incorrect index')

        if value == self.empty_element:
            if index in self.elements:
                del self.elements[index]
            if index in self.lists[0]:
                del self.lists[0][index]
        else:
            self.elements[index] = value
            hashed_element = self._calculate_hash(value)
            self.lists[0][index] = hashed_element

        levels = range(0, self.depth)
        indexs = [index // (2**power) for power in range(1, self.depth+1)]
        params = zip(levels, indexs)
        self.lists = reduce(self._calculate_and_update_leaf, params, self.lists)

    def add_element(self, index: int, value: bytes) -> None:
        if index not in self.elements:
            self.modify_element(index, value)
        else:
            raise KeyError('Value exist')

    def remove_element(self, index: int) -> None:
        if index in self.elements:
            self.modify_element(index, self.empty_element)
        else:
            raise KeyError('Value does not exist')

    @classmethod
    def _calculate_hash(cls, _) -> bytes:
        raise NotImplementedError("Please declare _calculate_hash")

class Sha256SparseMerkleTree(SparseMerkleTree):

    @classmethod
    def _calculate_hash(cls, preimage: bytes) -> bytes:
        return sha256(preimage).digest()
