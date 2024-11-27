def trigger_scene(osc, index):
    idx = int(index)

    if idx < 1:
        return


    osc.send_message("/hog/playback/go/1", idx)


def update_fader(osc, fader, value):
    val = int(value)

    if val < 0 or val > 255:
        return

    osc.send_message(f"/hog/hardware/fader/{fader}", val)
