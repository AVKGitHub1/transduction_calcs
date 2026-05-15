import numpy as np
from scipy.constants import epsilon_0, c, hbar, elementary_charge, physical_constants
from arc import Rubidium85

a0 = physical_constants["Bohr radius"][0]
e = elementary_charge

def rabi_frequency_Rb85_hfs(lower, upper, q, power_W, waist_m):
    """
    lower = (n, l, j, F, mF)
    upper = (n, l, j, F, mF)

    l convention:
      S=0, P=1, D=2, F=3, ...

    q:
      -1 = sigma-
       0 = pi
      +1 = sigma+

    power_W: beam power in W
    waist_m: Gaussian 1/e^2 waist radius in m
    """

    atom = Rubidium85()

    n1, l1, j1, F1, mF1 = lower
    n2, l2, j2, F2, mF2 = upper

    # Peak intensity at beam waist, on-axis
    I0 = 2 * power_W / (np.pi * waist_m**2)

    # Peak electric field amplitude
    E0 = np.sqrt(2 * I0 / (epsilon_0 * c))

    # Hyperfine-resolved dipole matrix element in units of e a0
    d_au = atom.getDipoleMatrixElementHFS(
        n1, l1, j1, F1, mF1,
        n2, l2, j2, F2, mF2,
        q
    )

    # Convert e a0 -> C m
    d_SI = abs(d_au) * e * a0

    # Angular Rabi frequency
    Omega_rad_s = d_SI * E0 / hbar
    Omega_Hz = Omega_rad_s / (2 * np.pi)

    return {
        "I0_W_m2": I0,
        "E0_V_m": E0,
        "dipole_ea0": d_au,
        "Omega_rad_s": Omega_rad_s,
        "Omega_Hz": Omega_Hz,
        "Omega_MHz": Omega_Hz / 1e6,
    }

import numpy as np
from arc import Rubidium85

def rabi_frequency_Rb85_fs(
    lower,
    upper,
    q,
    power_W,
    waist_m,
):
    """
    Calculate Rabi frequency for Rb85 without hyperfine structure.

    lower = (n, l, j, mj)
    upper = (n, l, j)

    q = +1 for sigma+
        0 for pi
       -1 for sigma-

    power_W: laser power in W
    waist_m: Gaussian 1/e^2 waist radius in m

    Returns angular Rabi frequency and ordinary frequency.
    """

    atom = Rubidium85()

    n1, l1, j1, mj1 = lower
    n2, l2, j2 = upper

    Omega_rad_s = atom.getRabiFrequency(
        n1, l1, j1, mj1,
        n2, l2, j2,
        q,
        laserPower=power_W,
        laserWaist=waist_m
    )

    return {
        "Omega_rad_s": Omega_rad_s,
        "Omega_Hz": Omega_rad_s / (2 * np.pi),
        "Omega_MHz": Omega_rad_s / (2 * np.pi * 1e6),
    }