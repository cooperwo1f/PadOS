import math

from lib.hog import trigger_scene
from lib.colour import COLOUR_WHEEL, split_compl, triac, analogous
from lib.modes import Mode

SYS_COL = 0xF000F0

primary_col = None
secondary_col = None

mode = Mode.MIX


def colour(con, x, y, r, g, b):
    msg = f"{y}{x}{int(r/4):02d}{int(g/4):02d}{int(b/4):02d}"
    con.sendall(msg.encode())


def colour_hex(con, x, y, col):
    b = col & 255
    g = (col >> 8) & 255
    r = (col >> 16) & 255
    colour(con, x, y, r/5, g/5, b/5)


def clear_all(con):
    colour(con, 9, 9, 0, 0, 0)


def colour_mode(con, mode):
    if mode is Mode.SESH:
        colour_hex(con, 5, 9, SYS_COL)
        colour(con, 6, 9, 0, 0, 0)
        colour(con, 7, 9, 0, 0, 0)
        colour(con, 8, 9, 0, 0, 0)

    elif mode is Mode.U1:
        colour_hex(con, 6, 9, SYS_COL)
        colour(con, 5, 9, 0, 0, 0)
        colour(con, 7, 9, 0, 0, 0)
        colour(con, 8, 9, 0, 0, 0)

    elif mode is Mode.U2:
        colour_hex(con, 7, 9, SYS_COL)
        colour(con, 5, 9, 0, 0, 0)
        colour(con, 6, 9, 0, 0, 0)
        colour(con, 8, 9, 0, 0, 0)

    elif mode is Mode.MIX:
        colour_hex(con, 8, 9, SYS_COL)
        colour(con, 5, 9, 0, 0, 0)
        colour(con, 6, 9, 0, 0, 0)
        colour(con, 7, 9, 0, 0, 0)


def static_secondaries(con):
    inc = int(len(COLOUR_WHEEL) / 8)
    end = len(COLOUR_WHEEL)

    for i, idx in enumerate(range(0, end, inc)):
        col = COLOUR_WHEEL[idx]
        colour_hex(con, i+1, 1, col)


def current_colours(con):
    clear_all(con)
    colour_mode(con, mode)
    # static_secondaries(con)

    for y in range(1, 4):
        idy = 9 - y

        for x in range(1, 9):
            c = COLOUR_WHEEL[(x-1) + ((y-1)*8)]
            colour_hex(con, x, idy, c)


def colour_relationships(con, col):
    t1, t2, t3 = triac(col)
    s1, s2, s3, s4, s5 = split_compl(col)
    a1, a2, a3, a4, a5, a6, a7 = analogous(col)

    colour_hex(con, 3, 3, t3)
    colour_hex(con, 4, 3, t2)
    colour_hex(con, 5, 3, t1)

    colour_hex(con, 2, 2, s5)
    colour_hex(con, 3, 2, s4)
    colour_hex(con, 4, 2, s3)
    colour_hex(con, 5, 2, s2)
    colour_hex(con, 6, 2, s1)

    colour_hex(con, 1, 1, a1)
    colour_hex(con, 2, 1, a2)
    colour_hex(con, 3, 1, a3)
    colour_hex(con, 4, 1, a4)
    colour_hex(con, 5, 1, a5)
    colour_hex(con, 6, 1, a6)
    colour_hex(con, 7, 1, a7)

    # static_secondaries(con)


def reset(con):
    global primary_col
    global secondary_col
    global mode

    primary_col = None
    secondary_col = None
    mode = Mode.MIX
    current_colours(con)


def scene_trigger(osc, colour, offset):
    ROW_WIDTH = 8
    ROW_SPACING = 2

    index = COLOUR_WHEEL.index(colour)
    row = math.ceil((index + 1) / ROW_WIDTH)

    idx = offset + index + ((row - 1) * ROW_SPACING)
    trigger_scene(osc, idx)


def pressed(osc, con, x, y, p):
    global primary_col
    global secondary_col
    global mode

    idx = int(x)
    idy = int(y)

    if idx < 1 or idx > 9 or idy < 1 or idy > 9:
        return


    if p:
        if idy == 9:
            if idx == 1:
                pass # UP

            if idx == 2:
                pass # DOWN

            if idx == 3:
                pass # LEFT

            if idx == 4:
                pass # RIGHT

            if idx == 5:
                mode = Mode.SESH


            elif idx == 6:
                mode = Mode.U1
                colour_mode(con, mode)

            elif idx == 7:
                mode = Mode.U2
                colour_mode(con, mode)

            elif idx == 8:
                mode = Mode.MIX
                colour_mode(con, mode)



        elif idx == 9:
            if idy == 1:
                reset(con)


        else:
            if mode is Mode.MIX:
                if idy >= 6:
                    primary_col = COLOUR_WHEEL[(idx-1) + (((9-idy)-1)*8)]
                    scene_trigger(osc, primary_col, 202)
                    colour_relationships(con, primary_col)

                if primary_col is not None:
                    if idy == 3:
                        if idx >= 3 and idx <= 5:
                            secondary_col = triac(primary_col)[abs(5-idx)]
                            scene_trigger(osc, secondary_col, 242)

                    elif idy == 2:
                        if idx >= 2 and idx <= 6:
                            secondary_col = split_compl(primary_col)[abs(6-idx)]
                            scene_trigger(osc, secondary_col, 242)

                    elif idy == 1:
                        if idx <= 7:
                            secondary_col = analogous(primary_col)[idx-1]
                            scene_trigger(osc, secondary_col, 242)
