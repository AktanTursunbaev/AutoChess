import random


def generate_pairs(players):
    if len(players) < 2:
        yield []
        return
    if len(players) % 2 == 1:
        for i in range(len(players)):
            for result in generate_pairs(players[:i] + players[i + 1:]):
                yield result + [(players[i], random.choice(players[:i] + players[i + 1:]))]
    else:
        a = players[0]
        for i in range(1, len(players)):
            pair = (a, players[i])
            for rest in generate_pairs(players[1:i] + players[i + 1:]):
                yield [pair] + rest
