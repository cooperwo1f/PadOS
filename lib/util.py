from lib.colour import COLOUR_WHEEL, split_compl, triac, analogous


def colour(con, x, y, r, g, b):
    msg = f"{y}{x}{int(r/4):02d}{int(g/4):02d}{int(b/4):02d}"
    con.sendall(msg.encode())


def colour_hex(con, x, y, col):
    b = col & 255
    g = (col >> 8) & 255
    r = (col >> 16) & 255
    colour(con, x, y, r, g, b)


def current_colours(con):
    for y in range(1, 4):
        idy = 9 - y

        for x in range(1, 9):
            c = COLOUR_WHEEL[(x-1) + ((y-1)*8)]
            colour_hex(con, x, idy, c)


def colour_relationships(con, col):
    t1, t2, t3 = triac(col)
    s1, s2, s3, s4, s5 = split_compl(col)
    a1, a2, a3, a4, a5, a6, a7 = analogous(col)

    # for x in range(1, 8):
    #     for y in range(1, 4):
    #         colour(con, x, y, 0, 0, 0)

    colour_hex(con, 3, 3, t1)
    colour_hex(con, 4, 3, t2)
    colour_hex(con, 5, 3, t3)

    colour_hex(con, 2, 2, s1)
    colour_hex(con, 3, 2, s2)
    colour_hex(con, 4, 2, s3)
    colour_hex(con, 5, 2, s4)
    colour_hex(con, 6, 2, s5)

    colour_hex(con, 1, 1, a7)
    colour_hex(con, 2, 1, a6)
    colour_hex(con, 3, 1, a5)
    colour_hex(con, 4, 1, a4)
    colour_hex(con, 5, 1, a3)
    colour_hex(con, 6, 1, a2)
    colour_hex(con, 7, 1, a1)


def pressed(con, x, y, p):
    idx = int(x)
    idy = int(y)

    if idx >= 1 and idx < 9:
        if idy >= 6 and idy < 9:
            if p:
                col = COLOUR_WHEEL[(idx-1) + (((9-idy)-1)*8)]
                colour_relationships(con, col)
