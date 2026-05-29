import numpy as np
from scipy.constants import epsilon_0, c, hbar, elementary_charge, physical_constants


# Fill these with the transition dipole moments in atomic units (e a0).
# Blue: 5P3/2, mj=3/2 -> 55S1/2 with q=-1
# UV:   5S1/2, mj=1/2 -> 54P3/2 with q=+1
d_b = -6.93809e-03
d_UV = 1.70762e-03


a0 = physical_constants["Bohr radius"][0]
e = elementary_charge

BLUE_TRANSITION = {
    "lower": (5, 1, 1.5, 1.5),
    "upper": (55, 0, 0.5),
    "q": -1,
    "dipole_name": "d_b",
}

UV_TRANSITION = {
    "lower": (5, 0, 0.5, 0.5),
    "upper": (54, 1, 1.5),
    "q": 1,
    "dipole_name": "d_UV",
}


def _peak_field_amplitude(power_W, waist_m):
    """Return on-axis electric-field amplitude for a Gaussian beam waist."""
    I0 = 2 * power_W / (np.pi * waist_m**2)
    E0 = np.sqrt(2 * I0 / (epsilon_0 * c))
    return I0, E0


def _dipole_si(dipole_ea0, dipole_name):
    if dipole_ea0 is None:
        raise ValueError(
            f"{dipole_name} is not set. Fill it in at the top of "
            "rabi_freq_HardCoded.py in units of e a0."
        )
    return abs(dipole_ea0) * e * a0


def _rabi_frequency_from_dipole(dipole_ea0, dipole_name, power_W, waist_m):
    I0, E0 = _peak_field_amplitude(power_W, waist_m)
    d_SI = _dipole_si(dipole_ea0, dipole_name)

    Omega_rad_s = d_SI * E0 / hbar
    Omega_Hz = Omega_rad_s / (2 * np.pi)

    return {
        "I0_W_m2": I0,
        "E0_V_m": E0,
        "dipole_ea0": dipole_ea0,
        "Omega_rad_s": Omega_rad_s,
        "Omega_Hz": Omega_Hz,
        "Omega_MHz": Omega_Hz / 1e6,
    }


def rabi_frequency_blue(power_W, waist_m):
    """Rabi frequency for the hard-coded blue transition."""
    return _rabi_frequency_from_dipole(d_b, "d_b", power_W, waist_m)


def rabi_frequency_UV(power_W, waist_m):
    """Rabi frequency for the hard-coded UV transition."""
    return _rabi_frequency_from_dipole(d_UV, "d_UV", power_W, waist_m)


def rabi_frequency_Rb85_fs(
    lower,
    upper,
    q,
    power_W,
    waist_m,
):
    """
    Calculate Rabi frequency for the known Rb85 transitions without ARC.

    This mirrors rabi_freq.rabi_frequency_Rb85_fs, but only supports the
    transitions listed at the top of this file. Dipole matrix elements are read
    from d_b and d_UV instead of being looked up through ARC at run time.
    """
    if (
        lower == BLUE_TRANSITION["lower"]
        and upper == BLUE_TRANSITION["upper"]
        and q == BLUE_TRANSITION["q"]
    ):
        return rabi_frequency_blue(power_W, waist_m)

    if (
        lower == UV_TRANSITION["lower"]
        and upper == UV_TRANSITION["upper"]
        and q == UV_TRANSITION["q"]
    ):
        return rabi_frequency_UV(power_W, waist_m)

    raise ValueError(
        "Unsupported hard-coded transition. Add its dipole moment and matching "
        "state tuple to rabi_freq_HardCoded.py."
    )


def rabi_frequency_Rb85_hfs(*args, **kwargs):
    """
    Import-compatible placeholder for the ARC-backed HFS helper.

    Add an HFS dipole constant and transition mapping if you need this path
    without ARC.
    """
    raise NotImplementedError(
        "Hard-coded HFS Rabi frequencies are not configured. Add the relevant "
        "dipole moment to rabi_freq_HardCoded.py before using this helper."
    )
