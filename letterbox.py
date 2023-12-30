"""Solves the NYTimes' Letterboxed puzzle."""
from collections.abc import Sequence
import dataclasses


@dataclasses.dataclass
class TrieNode:
    """Trie built from word dictionary."""
    letter: str = None
    children: dict[str, 'TrieNode'] = dataclasses.field(default_factory=dict)
    is_word: bool = False


def insert_word(node: TrieNode, word: str):
    """Add word to the trie."""
    if not word:
        node.is_word = True
        return
    letter, remainder = word[0], word[1:]
    if letter in node.children:
        insert_word(node.children[letter], remainder)
    else:
        child = TrieNode(letter=letter)
        node.children[letter] = child
        insert_word(child, remainder)


def dump_trie(trie: TrieNode, word: str):
    """Print the trie."""
    if trie.is_word:
        print(word)
    for letter, child in trie.children.items():
        dump_trie(child, ' ' + word + letter)


def build_trie(dictionary: Sequence[str], available_letters: set[str]):
    """Build trie incrementally. Filter out words that cannot be made from available letters."""
    trie = TrieNode()
    for word in dictionary:
        if '-' in word:
            # Not allowed by NYT rules.
            continue
        if not set(word).issubset(available_letters):
            continue
        insert_word(trie, word)
    return trie


@dataclasses.dataclass(frozen=True)
class Solution:
    """A (possibly partial) solution: """
    words: list[str]
    coverage: set[str]

    def length(self):
        """How many words in this solution."""
        return len(self.words)

    def coverage_length(self):
        """How many letters covered by this solution."""
        return len(self.coverage)

    def solves(self, available_letters: set[str]) -> bool:
        """Whether this solution can solve the puzzle by covering all letters."""
        return self.coverage == available_letters


def find_words(sides: Sequence[str], word: str, word_node: TrieNode, from_side: int):
    """Find all words."""
    results = []
    for side_index, side in enumerate(sides):
        if side_index == from_side:
            continue
        for letter in side:
            if letter not in word_node.children:
                continue
            results.extend(find_words(sides, word + letter,
                           word_node.children[letter], side_index))
    if word_node.is_word and len(word) >= 3:
        results.append((from_side, word))
    return results


@dataclasses.dataclass
class Solutions:
    """All solutions found to the puzzle, by length (number of words)."""
    by_length: dict[int, list[Solution]
                    ] = dataclasses.field(default_factory=dict)

    def insert(self, solution: Solution):
        """Insert a new solution."""
        self.by_length.setdefault(solution.length(), []).append(solution)

    def count(self, for_length: int):
        """How many solutions for """
        if for_length not in self.by_length:
            return 0
        return len(self.by_length[for_length])


class Puzzle:
    """A instance of the puzzle to solve."""
    all_letters: set[str]
    sides: Sequence[str]
    trie_root: TrieNode

    def __init__(self, dictionary, sides: Sequence[str]):
        self.all_letters = {letter for side in sides for letter in side}
        self.sides = sides
        self.trie_root = build_trie(dictionary, self.all_letters)


def find_solutions(solutions: Solutions,
                   puzzle: Puzzle,
                   current_solution: Solution,
                   starting_letter: str,
                   starting_side: int):
    """Find all solutions to a puzzle."""
    # Limit the search space
    max_count = 10
    max_length = 4
    # Only add the current word if it increases the coverage. We make the assumption that there exists a solution
    # that doesn't require us to "spend" a word that doesn't increase the number of covered letters here. Otherwise
    # we might end up with very long solution sequences.
    only_increase_coverage = True

    word_node = puzzle.trie_root.children.get(starting_letter)
    if word_node is None:
        return

    # We don't want solutions longer than 4.
    if current_solution.length() >= max_length:
        return

    # Do we already have enough solutions with the length we're about to search for?
    if solutions.count(current_solution.length() + 1) >= max_count:
        return

    # Try extending the current word first
    all_words = find_words(puzzle.sides, starting_letter,
                           word_node, starting_side)
    # Greedy algorithm: search the longest words first.
    all_words.sort(key=lambda x: len(x[1]), reverse=True)

    for new_side, new_word in all_words:
        updated_coverage = current_solution.coverage | set(new_word)
        if only_increase_coverage and len(updated_coverage) <= current_solution.coverage_length():
            return
        s = Solution(current_solution.words + [new_word], updated_coverage)
        if s.solves(puzzle.all_letters):
            solutions.insert(s)
            return

        # Start searching from the last letter of the new word.
        new_node = puzzle.trie_root.children.get(new_word[-1])
        if new_node is not None:
            find_solutions(solutions, puzzle, s, new_word[-1], new_side)


def main():
    with open('safedict_simple.txt', 'r') as f:
        dictionary = f.readlines()
    dictionary = [x.rstrip() for x in dictionary]

    # Today's problem.
    sides = ['atr', 'guf', 'qin', 'lec']

    puzzle = Puzzle(dictionary, sides)
    solutions = Solutions()
    for side_index, letters in enumerate(sides):
        for letter in letters:
            if letter not in puzzle.trie_root.children:
                continue
            find_solutions(solutions, puzzle, Solution(
                words=[], coverage=set()), letter, side_index)
    print('Solutions:')
    for length in sorted(solutions.by_length):
        sols = solutions.by_length[length]
        print(f'Length {length}: {len(sols)}')
        for s in sols:
            print(s.words)


main()
