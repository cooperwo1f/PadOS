COLOUR_WHEEL = [
    0x00FFFF, 0x00BFFF, 0x0080FF, 0x0040FF, 0x0000BF, 0x4000FF, 0x8000FF, 0xBF00FF,
    0xFF00FF, 0xFF00BF, 0xFF0080, 0xFF0040, 0xBF0000, 0xFF4000, 0xFF8000, 0xFFBF00,
    0xFFFF00, 0xBFFF00, 0x80FF00, 0x40FF00, 0x00BF00, 0x00FF40, 0x00FF80, 0x00FFBF
]

def split_compl(colour):
    index = COLOUR_WHEEL.index(colour)
    compl_idx = int((len(COLOUR_WHEEL) / 2) + index) % len(COLOUR_WHEEL)

    c1_idx = (compl_idx - 2) % len(COLOUR_WHEEL)
    c2_idx = (compl_idx - 1) % len(COLOUR_WHEEL)
    c4_idx = (compl_idx + 1) % len(COLOUR_WHEEL)
    c5_idx = (compl_idx + 2) % len(COLOUR_WHEEL)

    return COLOUR_WHEEL[c1_idx], COLOUR_WHEEL[c2_idx], COLOUR_WHEEL[compl_idx], COLOUR_WHEEL[c4_idx], COLOUR_WHEEL[c5_idx]


def triac(colour):
    index = COLOUR_WHEEL.index(colour)

    c1_idx = int(index + len(COLOUR_WHEEL) / 3) % len(COLOUR_WHEEL)
    c3_idx = int(index - len(COLOUR_WHEEL) / 3) % len(COLOUR_WHEEL)
    return COLOUR_WHEEL[c1_idx], COLOUR_WHEEL[index], COLOUR_WHEEL[c3_idx]


def analogous(colour):
    index = COLOUR_WHEEL.index(colour)

    c1 = COLOUR_WHEEL[(index - 3) % len(COLOUR_WHEEL)]
    c2 = COLOUR_WHEEL[(index - 2) % len(COLOUR_WHEEL)]
    c3 = COLOUR_WHEEL[(index - 1) % len(COLOUR_WHEEL)]
    c5 = COLOUR_WHEEL[(index + 1) % len(COLOUR_WHEEL)]
    c6 = COLOUR_WHEEL[(index + 2) % len(COLOUR_WHEEL)]
    c7 = COLOUR_WHEEL[(index + 3) % len(COLOUR_WHEEL)]

    return c1, c2, c3, COLOUR_WHEEL[index], c5, c6, c7
