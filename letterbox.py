"""Solves the NYTimes' Letterboxed puzzle."""
from collections.abc import Sequence
import dataclasses
import functools


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


def find_words(sides: Sequence[str], word: str, word_node: TrieNode, from_side: int) -> list[str]:
    """Find all valid words from a prefix."""
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
        results.append(word)
    return results


@dataclasses.dataclass
class Solutions:
    """All solutions to the puzzle found so far, by length (number of words)."""
    by_length: dict[int, list[Solution]
                    ] = dataclasses.field(default_factory=dict)

    # All words found so far, by length.
    words_so_far_by_length: dict[int, set[str]
                                 ] = dataclasses.field(default_factory=dict)

    def insert(self, solution: Solution):
        """Insert a new solution."""
        self.by_length.setdefault(solution.length(), []).append(solution)
        self.words_so_far_by_length.setdefault(
            solution.length(), set()).update(solution.words)

    def count(self, for_length: int) -> int:
        """How many solutions of given length."""
        if for_length not in self.by_length:
            return 0
        return len(self.by_length[for_length])

    def words_so_far(self, for_length: int) -> set[str]:
        if for_length not in self.words_so_far_by_length:
            return set()
        return self.words_so_far_by_length[for_length]


class Puzzle:
    """A instance of the puzzle to solve."""
    all_letters = set[str]
    all_possible_words: dict[str, list[str]]

    def __init__(self, dictionary, sides: Sequence[str]):
        self.all_letters = {letter for side in sides for letter in side}
        trie = build_trie(dictionary, self.all_letters)
        # Build the list of all possible words for each starting letter.
        self.all_possible_words = {}
        for i, side in enumerate(sides):
            for letter in side:
                words = []
                if letter not in trie.children:
                    continue
                words.extend(find_words(
                    sides, letter, trie.children[letter], from_side=i))
                # Put the longest words first.
                words.sort(key=len, reverse=True)
                self.all_possible_words[letter] = words


def find_solutions(solutions: Solutions,
                   puzzle: Puzzle,
                   current_solution: Solution,
                   starting_letter: str):
    """Find all solutions to a puzzle."""
    # Limit the search space.
    max_count = 10
    max_length = 5
    # Only add the current word if it increases the coverage. We make the assumption that there exists a solution
    # that doesn't require us to "spend" a word that doesn't increase the number of covered letters here. Otherwise
    # we might end up with very long solution sequences.
    only_increase_coverage = True

    # We don't want solutions longer than 4.
    if current_solution.length() >= max_length:
        return

    # Do we already have enough solutions with the length we're about to search for?
    if solutions.count(current_solution.length() + 1) >= max_count:
        return

    # Find all words that can be made from the starting letter.
    all_words = puzzle.all_possible_words[starting_letter]

    for new_word in all_words:
        updated_coverage = current_solution.coverage | set(new_word)
        if only_increase_coverage and len(updated_coverage) <= current_solution.coverage_length():
            return
        s = Solution(current_solution.words + [new_word], updated_coverage)
        # Only add the solution if all of its words haven't been found yet.
        words_found = solutions.words_so_far(s.length())
        if any(word in words_found for word in s.words):
            continue

        if s.solves(puzzle.all_letters):
            solutions.insert(s)
            return
        # Start searching from the last letter of the new word.
        find_solutions(solutions, puzzle, s, new_word[-1])


def main():
    with open('safedict_simple.txt', 'r') as f:
        dictionary = f.readlines()
    dictionary = [x.rstrip() for x in dictionary]

    # Today's problem.
    sides = ['btl', 'ehy', 'ocv', 'jwi']

    puzzle = Puzzle(dictionary, sides)
    solutions = Solutions()
    for side in sides:
        for letter in side:
            find_solutions(solutions, puzzle, Solution(
                words=[], coverage=set()), letter)
    print('Solutions:')
    for length in sorted(solutions.by_length):
        sols = solutions.by_length[length]
        print(f'Length {length}: {len(sols)}')
        for s in sols:
            print(s.words)


main()
