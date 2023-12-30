
def main():
    with open('safedict_simple.txt', 'r') as f:
        dictionary = f.readlines()
    dictionary = [x.rstrip() for x in dictionary]

    # Today's problem.
    center_letter = 'r'
    other_letters = 'iocazn'
    all_letters = set(center_letter) | set(other_letters)

    # Find all words that can be made with at least one of the center letter and only the available letters.
    matches = []
    for word in dictionary:
        if len(word) >= 4 and center_letter in word and all_letters.issuperset(word):
            matches.append(word)
    matches.sort(key=len)
    print(matches)


main()
