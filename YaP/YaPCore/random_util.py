import random

def seeded_randchoice(c, seed):
    random.seed(seed)
    return random.choice(c)

def seeded_randint(x1, x2, seed):
    random.seed(seed)
    return random.randint(x1,x2)

def seeded_shuffle(x,seed):
    xc = x.copy()
    random.seed(seed)
    random.shuffle(xc)
    return xc

def random_sequence(length, charset):
    return "".join(random.choice(charset) for _ in range(length))

def seeded_shuffle_str(x,seed):
    l = seeded_shuffle(list(x),seed)
    return "".join(l)