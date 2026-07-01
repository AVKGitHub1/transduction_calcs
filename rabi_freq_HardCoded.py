import numpy as np
from scipy.constants import epsilon_0, c, hbar, elementary_charge, physical_constants


# Fill these with the transition dipole moments in atomic units (e a0).
# Blue: 5P3/2, mj=3/2 -> 55S1/2 with q=-1
# UV:   5S1/2, mj=1/2 -> 54P3/2 with q=+1
# Opt:  5S1/2, mj=1/2 -> 5P3/2, mj=3/2 with q=+1
d_b = -6.938086e-03
d_UV = -1.394265e-03
d_opt = 2.989150e+00

OPTICAL_CAVITY_WAVELENGTH_M = 780.24e-9


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


def single_atom_coupling_from_mode_volume(
    dipole_ea0,
    wavelength_m,
    mode_volume_m3,
    dipole_name="dipole_ea0",
):
    """
    Calculate the single-atom vacuum coupling g for a cavity mode.

    The mode volume must be in m^3. The returned ``g_rad_s`` is angular
    frequency, while ``g_Hz``, ``g_kHz``, and ``g_MHz`` are g / (2 pi).
    """
    if wavelength_m <= 0:
        raise ValueError("wavelength_m must be greater than zero.")
    if mode_volume_m3 <= 0:
        raise ValueError("mode_volume_m3 must be greater than zero.")

    d_SI = _dipole_si(dipole_ea0, dipole_name)
    omega_rad_s = 2 * np.pi * c / wavelength_m
    vacuum_field_V_m = np.sqrt(
        hbar * omega_rad_s / (2 * epsilon_0 * mode_volume_m3)
    )
    g_rad_s = d_SI * vacuum_field_V_m / hbar
    g_Hz = g_rad_s / (2 * np.pi)

    return {
        "dipole_ea0": dipole_ea0,
        "wavelength_m": wavelength_m,
        "mode_volume_m3": mode_volume_m3,
        "vacuum_field_V_m": vacuum_field_V_m,
        "g_rad_s": g_rad_s,
        "g_Hz": g_Hz,
        "g_kHz": g_Hz / 1e3,
        "g_MHz": g_Hz / 1e6,
    }


def single_atom_g_optical(mode_volume_m3):
    """Single-atom g for the hard-coded 780.24 nm optical transition."""
    return single_atom_coupling_from_mode_volume(
        d_opt,
        OPTICAL_CAVITY_WAVELENGTH_M,
        mode_volume_m3,
        "d_opt",
    )


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
