import sys
import numpy as np
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

from sklearn.gaussian_process.kernels import RBF, Matern

#def get_xangle(u,deg=None):
#    v = np.array([1,0])
#    cosang = np.dot(u, v)
#    sinang = np.linalg.norm(np.cross(u, v))
#    if deg:
#       return np.rad2deg(np.arctan2(sinang, cosang))
##   else:
#        return np.arctan2(sinang, cosang)
def determinant(v,w):
   return v[0]*w[1]-v[1]*w[0]
def angle_clockwise(A, B):
    #print(np.arccos(np.dot(A,B) / (np.linalg.norm(A)*np.linalg.norm(B)))*180/np.pi)
    #print("="*60)
    #inner_angle = np.arccos(np.dot(A,B) / (np.linalg.norm(A)*np.linalg.norm(B)))
    inner_angle = np.arccos(np.clip(np.dot(A,B) / (np.linalg.norm(A)*np.linalg.norm(B)),-1,1))
    det = determinant(A,B)
    if det<0: #this is a property of the det. If the det < 0 then B is clockwise of A
        return inner_angle
    else: # if the det > 0 then A is immediately clockwise of B
        return 2*np.pi-inner_angle

def create_bases(mean, n_base, len_base, var_base, base_type, \
                 plot=False):
    base = np.zeros((n_base, len_base, 2))
    base[:,0,:] = mean[0]
    mean_indices = [int(el) for el in np.linspace(1,len(mean)-1,len_base)]
    var_indices = [int(el) for el in np.linspace(1,len(var_base)-1,len_base)]

    for i in range(len_base):
        i_mean = mean_indices[i]
        i_var = var_indices[i]

        theta = angle_clockwise(mean[i_mean],mean[i_mean-1])+0.5*np.pi
        Phi = np.array([[np.cos(theta), -np.sin(theta)],\
                        [np.sin(theta), np.cos(theta)]])

        line = np.zeros((n_base,2))
        if base_type == "Linear":
            line[:,0] = np.linspace(-var_base[i_var],var_base[i_var],n_base)
        elif base_type ==  "Normal":
            line[:,0] = np.sort(np.random.normal(0, var_base[i_var], \
                                                 n_base))
        elif base_type ==  "Uniform":
            line[:,0] = np.sort(np.random.uniform(-var_base[i_var], \
                                            var_base[i_var], n_base))
        else:
            print("Invalid base_type: ",base_type)
            sys.exit()

        rot = mean[i_mean] + np.matmul(Phi,line.T).T
        base[:,i,0] = rot[:,0]
        base[:,i,1] = rot[:,1]
    if plot:
        fig = plt.figure(figsize=(16,9))
        ax1 = fig.add_subplot(111)
        ax1.plot(mean[:,0],mean[:,1],c="k",linewidth=2,linestyle="--")
        for n in range(n_base):
            #ax1.scatter(base[n,:,0],base[n,:,1])
            ax1.plot(base[n,:,0],base[n,:,1])
        ax1.set_aspect("equal")
        ax1.set_title("Base Trajectories")
        plt.show()
    return base

def adjust_base_length(base, len_total, plot=False):
    adj_bases = np.zeros((base.shape[0], len_total, 2))
    for i in range(base.shape[0]):
        t = np.arange(base.shape[1])
        ti = np.linspace(t.min(), t.max(), len_total)
        fx = interp1d(t, base[i,:,0])
        fy = interp1d(t, base[i,:,1])
        adj_bases[i,:,0] = fx(ti)
        adj_bases[i,:,1] = fy(ti)
    if plot:
        fig = plt.figure(figsize=(16,9))
        ax = fig.add_subplot(111)
        for n in range(base.shape[0]):
            ax.scatter(adj_bases[n,:,0],adj_bases[n,:,1])
        for n in range(base.shape[0]):
            ax.plot(adj_bases[n,:,0],adj_bases[n,:,1])
        ax.set_aspect("equal")
        ax.set_title("Adjusted Base Trajectories")
        plt.show()
    return adj_bases


def create_samples(n_sample, len_sample, length_scale, total_scale,\
                   kind="RBF", plot=False):
    mean=np.zeros(len_sample)
    if kind == "RBF":
        cov = RBF(length_scale=length_scale)\
                                (np.arange(len_sample)[:,np.newaxis])
    elif kind == "Matern":
        cov = Matern(length_scale=length_scale)\
                                (np.arange(len_sample)[:,np.newaxis])
    samples = np.zeros((n_sample,len_sample,2))
    samples[:,:,0] = np.random.multivariate_normal(mean=mean, \
                                cov=cov, size=n_sample)*total_scale
    if plot:
        fig = plt.figure(figsize=(12,12))
        ax = fig.add_subplot(111)
        for i in range(n_sample):
            ax.plot(samples[i,:,0])
        ax.set_title("Sample Trajectories")
        plt.show()
    return samples

def combine(base, samples, mean, plot):
    n_per_base = int(samples.shape[0]/base.shape[0])
    combined = np.zeros((samples.shape[0],samples.shape[1],2))
    for i_sample in range(samples.shape[0]):
        i_base = i_sample // n_per_base
        combined[i_sample,0,:] = base[i_base,0,:]
        
        for i in range(1,samples.shape[1]):
            theta = angle_clockwise(base[i_base,i],base[i_base,i-1])+0.5*np.pi            
            Phi = np.array([[np.cos(theta), -np.sin(theta)],[np.sin(theta), np.cos(theta)]])
            combined[i_sample,i,:] = base[i_base,i] + np.matmul(Phi,samples[i_sample,i])
    if plot:
        fig = plt.figure(figsize=(16,9))
        ax = fig.add_subplot(111)
        for n in range(combined.shape[0]):
            ax.plot(combined[n,:,0],combined[n,:,1])
        for n in range(base.shape[0]):
            ax.scatter(base[n,:,0],base[n,:,1],alpha=.2)  
        ax.plot(mean[:,0],mean[:,1],c="k",linewidth=2,linestyle="--")
        ax.set_aspect("equal")
        ax.set_title("Final Trajectories")
        plt.show()        
    return combined

#def create_trajectories(mean, n_sample, len_sample, n_base, \
#                        len_base, base_type, var_base, \
#                        length_scale, total_scale, kind="RBF", \
#                        plot=False):
def create_trajectories(x_mean, y_mean, config):
    mean = np.vstack([x_mean,y_mean]).T
    n_total = config["n_total"]
    len_total = config["len_total"]
    n_base = config["n_base"]
    len_base = config["len_base"]
    base_type = config["base_type"]
    var_base = np.load(config["base_path"])
    length_scale = config["length_scale"]
    total_scale = config["scale"]
    kind = config["cov_type"]
    plot = False
    
    assert(n_total%n_base == 0)
    bases = create_bases(mean, n_base, len_base, var_base, \
                         base_type, plot)
    adj_bases = adjust_base_length(bases, len_total, plot)
    samples = create_samples(n_total, len_total, length_scale, \
                             total_scale, kind, plot)
    return combine(adj_bases, samples, mean, plot)
