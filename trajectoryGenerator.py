import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import configparser
from argparse import ArgumentParser

import wx
import sqlite3 as sql

import h5py

from gui.trajectoryGeneratorFrame import TrajectoryGeneratorGui

# from mapCreation import image2array
# from validation import validate_trace
# from noiseGeneration import add_simple_noise
# from walker.interpolatedWalk import interpolated_walk
# from walker.simulatedWalk import SimulatedWalker

def generate_walk(config, batch=False):
    # VALIDATION of CONFIG
    simCount = 0
    x = config["x"][:] #[:] necessary for copying instead of just
    y = config["y"][:] #referencing the lists
    worldMap = image2array(config["path"])
    if not validate_trace(x,y,worldMap, batch):
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
        if validate_trace(xs, ys, worldMap, batch):
            # return xs, ys, worldMap #nur zum Test
            xfinal, yfinal = add_simple_noise(xs, ys, config["post_noise"])
            pos = np.array([xfinal, yfinal]).T

            vx = (xfinal - np.roll(xfinal,1))[1:]
            vy = (yfinal - np.roll(yfinal,1))[1:]
            vel = np.array([vx, vy]).T

            ax = (vx - np.roll(vx,1))[1:]
            ay = (vy - np.roll(vy,1))[1:]
            acc = np.array([ax, ay]).T
            return pos, vel, acc

        simCount += 1
    print("Could not create a valid walk...I TRIED!!")
    return

def batch_walk(path):
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
                pos, vel, acc = generate_walk(config, batch=True)
                grp.create_dataset("Positions", data=pos)
                grp.create_dataset("Velocity", data=vel)
                grp.create_dataset("Acceleration", data=acc)
                for key in [key for key in config if key != "nr_runs"]:
                    grp.attrs[key] = config[key]
                count += 1
        grp_im = f.create_group("Images")
        grp_im.attrs["Type"] = "Images"
        im = cv2.imread(simulations[0]["path"])
        grp_im.create_dataset("OriginalFrame", data=im)
        grp_im.create_dataset("OriginalGoals", data=im)
        comment = ""
        for i, config_dict in enumerate(simulations):
            comment += "Simulation Nr. "+str(i)+":\n"
            for key in config_dict:
                comment += str(key)+":"+str(config_dict[key])+", "
            comment = comment[:-2]+"\n"
        f.attrs["Comment"] = comment
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

    root_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.sep.join([root_path,".data.db"])
    #Validieren / bekommen

    app = wx.App()
    TGG = TrajectoryGeneratorGui(None, wx.ID_ANY, db_path)
    # SWG.empty_setup()
    app.MainLoop()

    # AP = ArgumentParser()
    # AP.add_argument('-d', '--demo', action='store_true')
    # AP.add_argument('-b', '--batch')
    # args = AP.parse_args()
    # if args.batch:
    #     if args.batch[-6:] == ".batch":
    #         batch_walk(args.batch)
    # else:
    #     app = wx.App()
    #     SWG = TrajectoryGeneratorGui()
    #     if args.demo:
    #         SWG.demo_setup()
    #     else:
    #         SWG.empty_setup()
        # app.MainLoop()
