import numpy as np
import matplotlib.pyplot as plt

from helper_funcs import efficiency_func_OtoM, efficiency_plotter
from rabi_freq import rabi_frequency_Rb85_hfs, rabi_frequency_Rb85_fs

# Units: m, W, MHz

def run_test():
    # ExperimentParameters
    # Cavity Parameters
    gopt = 0.025
    gmm = 0.091
    kappaOpt = 10.0
    kappaMM = 10.0

    # Atom Parameters
    Natoms = 5e5
    AtomRadius = 250e-6
    gammaOpt = 6.0
    gammaMM = 0.100
    

    # Beam Parameters
    BeamSizeMultiplier = 5
    PowerUV = 1
    PowerBlue = 0.5
    WaistUV = BeamSizeMultiplier * AtomRadius
    WaistBlue = BeamSizeMultiplier * AtomRadius
    ground_state = (5, 0, 0.5, 0.5)
    excited_state = (5, 1, 1.5, 1.5)
    rydberg_r_state = (55, 0, 0.5)
    rydberg_f_state = (54, 1, 1.5)

    OmegaB = 1.45 / 2
    OmegaB = rabi_frequency_Rb85_fs(excited_state, rydberg_r_state, -1, PowerBlue, WaistBlue)["Omega_MHz"]
    FBlue = 100.0

    OmegaUV = 0.03
    OmegaUV = rabi_frequency_Rb85_fs(ground_state, rydberg_f_state, 1, PowerUV, WaistUV)["Omega_MHz"]
    DeltaUV = 5

    # Derived Parameters
    thetaUV = np.arctan(abs(OmegaUV / DeltaUV))

    Nmm = Natoms * np.sin(thetaUV) ** 2
    Nopt = Natoms * np.cos(thetaUV) ** 2

    Gopt = gopt * np.sqrt(Nopt)
    Gmm = gmm * np.sqrt(Nmm)

    params = dict(
        Gopt=Gopt,
        Gmm=Gmm,
        kappaOpt=kappaOpt,
        GammaOpt=gammaOpt,
        Delta_e=0.0,
        Delta_r=0.0,
        gammaMM=gammaMM,
        kappaMM=kappaMM,
        DeltaMM=0.0,
        OmegaB=np.sqrt(FBlue / np.pi) * OmegaB,
        Ein=1.0,
        epsilon=1.0,
    )
    fig, ax = efficiency_plotter(-10, 10, 1000, params)
    plt.show()

if __name__ == "__main__":
    run_test()