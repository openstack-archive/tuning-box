import collections
import decimal
import json
import os
import shutil
import sys

def remove_bs(data):
    new_stdout = []
    for i, e in enumerate(data["stdout"]):
        if '\b' in e[1]:
            c = e[1].count('\b')
            for j, e1 in enumerate(reversed(new_stdout)):
                if len(e1[1]) <= c:
                    c -= len(e1[1])
                    if not c:
                        break
                else:
                    e1[1] = e1[1][:-c]
                    j += 1
                    break
            new_stdout[-j-1:] = []
        else:
            new_stdout.append(e)
    data["stdout"] = new_stdout


def speedup_typing(data, delay):
    delay = decimal.Decimal(delay)
    it = iter(data["stdout"])
    try:
        e = next(it)
        while True:
            while not e[1].endswith("]# "):
                e = next(it)
            e = next(it)
            if e[1] != "#":
                continue
            while True:
                e = next(it)
                e[0] = delay
                if '\r' in e[1]:
                    break
    except StopIteration:
        pass


def set_max_delay(data, delay):
    delay = decimal.Decimal(delay)
    for e in data["stdout"]:
        if e[0] > delay:
            e[0] = delay


def correct_duration(data):
    data["duration"] = sum(e[0] for e in data["stdout"])


def main(fname):
    with open(fname) as f:
        data = json.load(f, object_pairs_hook=collections.OrderedDict, parse_float=decimal.Decimal)

    remove_bs(data)
    speedup_typing(data, '0.05')
    set_max_delay(data, '0.5')
    correct_duration(data)

    shutil.copy(fname, fname + ".tmp")
    with open(fname + ".tmp", "w") as f:
        data = json.dump(data, f, indent=2, cls=Encoder)
    os.rename(fname + ".tmp", fname)


class DecIntWrapper(int):
    def __init__(self, d):
        self.d = d

    def __str__(self):
        return str(self.d)


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            #import pdb; pdb.set_trace()
            return DecIntWrapper(o)
        return json.JSONEncoder.default(o)

if __name__ == '__main__':
    main(sys.argv[1])
