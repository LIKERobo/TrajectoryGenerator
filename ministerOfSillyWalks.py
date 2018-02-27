import os
import cv2
import numpy as np

import h5py

from mapCreation import image2array
from validation import validate_trace
from noiseGeneration import add_simple_noise
from walker.interpolatedWalk import interpolated_walk
from walker.simulatedWalk import SimulatedWalker

def generate_walk(config):
    # VALIDATION of CONFIG
    simCount = 0
    x = config["x"][:] #[:] necessary for copying instead of just
    y = config["y"][:] #referencing the lists
    worldMap = image2array(config["path"])
    if not validate_trace(x,y,worldMap):
        print("Invalid Initial Trace")
        return
    while simCount <= 100:
        xn, yn = add_simple_noise(x, y, config["pre_noise"])
        if config["method"] == "Interpolation":
            xs, ys = interpolated_walk(xn, yn, factor=config["factor"],\
                                       kind=config["kind"])
        elif config["method"] == "Simulation":
            JohnCleese = SimulatedWalker(xn, yn, config)
            xs, ys = JohnCleese.run_simulation()
        else:
            print("Invalid Method-Option: ",config["Method"])
            return
        if validate_trace(xs, ys, worldMap):
            # return xs, ys, worldMap #nur zum Test
            xfinal, yfinal = add_simple_noise(xs, ys, config["post_noise"])
            return xfinal, yfinal
        simCount += 1
    print("Could not create a valid walk...I TRIED!!")
    return

def batch_walk(path):
    from matplotlib import pyplot as plt
    simulations = read_config_file(path)
    count = 0
    out_path = os.path.split(path)[-1].split(".")[0]+".hdf5"
    with h5py.File(out_path, "w") as f:
        for config in simulations:
            for n in range(config["nr_runs"]):
                label = config["Goal"]
                if label not in f.keys():
                    new_grp = f.create_group(label)
                    new_grp.attrs["Type"] = "Trajectory"
                grp = f[label].create_group(str(count+1))
                xn, yn = generate_walk(config)
                data = np.array([xn,yn]).T
                grp.create_dataset("Positions", data=data)
                for key in [key for key in config if key != "nr_runs"]:
                    grp.attrs[key] = config[key]
                count += 1
        grp_im = f.create_group("Images")
        grp_im.attrs["Type"] = "Images"
        im = cv2.imread(simulations[0]["path"])
        grp_im.create_dataset("OriginalFrame", data=im)
        grp_im.create_dataset("OriginalGoals", data=im)
    print("Done...")

def read_config_file(path):
    try:
        simulations = []
        with open(path, "r") as f:
            for line in f.readlines():
                if line and not line.startswith("#"):
                    p = [el.strip() for el in line.strip().split(",")]
                    config = {}
                    config["Goal"] = p[0]
                    config["Origin"] = p[1]
                    config["nr_runs"] = int(p[2])
                    config["method"] = p[3]
                    config["kind"] = p[4]
                    config["factor"] = int(p[5])
                    config["pre_noise"] = float(p[6])
                    config["post_noise"] = float(p[7])
                    config["path"] = p[8]
                    config["x"] = np.fromstring(p[9][1:-1], sep=" ")
                    config["y"] = np.fromstring(p[10][1:-1], sep=" ")
                    assert len(config["x"]) == len(config["y"])
                    simulations.append(config)
        return simulations
    except FileNotFoundError:
        print("Input-File not found...")

if __name__ == "__main__":
    batch_walk("ideal.batch")
