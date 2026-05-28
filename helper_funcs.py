import numpy as np
import matplotlib.pyplot as plt

def efficiency_func_OtoM(
    omega,
    Gopt,
    Gmm,
    kappaOpt,
    kappaMM,
    GammaOpt,
    gammaMM,
    OmegaB,
    Delta_e,
    Delta_r,
    DeltaMM,
    Ein,
    epsilon,
):
    omega = np.asarray(omega, dtype=float)

    A = GammaOpt * kappaOpt + 2 * epsilon**2 * (
        Gopt**2 + 2 * (Delta_e - omega) * omega
    )

    B = -Delta_e * kappaOpt + (GammaOpt + kappaOpt) * omega

    C = (
        4 * epsilon**2 * (Delta_r - omega) * B
        + gammaMM * A
        + 4 * epsilon**2 * kappaOpt * OmegaB**2
    )

    D = (
        gammaMM * (
            -2 * Delta_e * epsilon * kappaOpt
            + 2 * epsilon * (GammaOpt + kappaOpt) * omega
        )
        - 2 * epsilon * (Delta_r - omega) * A
        + 8 * epsilon**3 * omega * OmegaB**2
    )

    denom_real = (
        4 * Gmm**2 * epsilon**3
        * (Delta_e * kappaOpt - (GammaOpt + kappaOpt) * omega)
        + 2 * epsilon * (DeltaMM - omega) * C
        + (-gammaMM - kappaMM) * D
    )

    denom_imag = (
        2 * Gmm**2 * epsilon**2 * A
        - (-gammaMM - kappaMM) * C
        + 2 * epsilon * (DeltaMM - omega) * D
    )

    numerator = (
        64
        * Ein**2
        * Gopt**2
        * Gmm**2
        * epsilon**8
        * kappaOpt
        * kappaMM
        * OmegaB**2
    )

    denominator = denom_real**2 + denom_imag**2

    return numerator / denominator

def efficiency_func_MtoO(
    omega,
    Gopt,
    Gmm,
    kappaOpt,
    kappaMM,
    GammaOpt,
    gammaMM,
    OmegaB,
    Delta_e,
    Delta_r,
    DeltaMM,
    Ein,
    epsilon,
):
    omega = np.asarray(omega, dtype=float)

    # Repeated blocks
    A = gammaMM * (gammaMM + kappaMM) + 2 * epsilon**2 * (
        Gmm**2 + 2 * (Delta_r - omega) * (-DeltaMM + omega)
    )

    B = gammaMM * (Delta_r + DeltaMM - 2 * omega) + kappaMM * (
        Delta_r - omega
    )

    C = (
        GammaOpt * B
        + (Delta_e - omega) * A
        + 4 * epsilon**2 * (DeltaMM - omega) * OmegaB**2
    )

    D = (
        GammaOpt * A
        + 4 * epsilon**2 * (
            B * (-Delta_e + omega)
            + (gammaMM + kappaMM) * OmegaB**2
        )
    )

    denom_real = (
        2 * Gopt**2 * epsilon**2 * A
        + 4 * epsilon**2 * omega * C
        + kappaOpt * D
    )

    denom_imag = (
        4 * Gopt**2 * epsilon**3 * B
        + 2 * epsilon * kappaOpt * C
        - 2 * epsilon * omega * D
    )

    numerator = (
        64
        * Ein**2
        * Gopt**2
        * Gmm**2
        * epsilon**8
        * kappaOpt
        * kappaMM
        * OmegaB**2
    )

    denominator = denom_real**2 + denom_imag**2

    return numerator / denominator

def efficiency_func_2(
    omega,
    Gopt,
    Gmm,
    kappaOpt,
    kappaMM,
    GammaOpt,
    gammaMM,
    OmegaB,
    Delta_e,
    Delta_r,
    DeltaMM,
    Ein,
    epsilon,
):
    omega = np.asarray(omega, dtype=float)

    A = GammaOpt * kappaOpt + 2 * epsilon**2 * (
        Gopt**2 + 2 * (Delta_e - omega) * omega
    )

    B = -Delta_e * kappaOpt + (GammaOpt + kappaOpt) * omega

    C = (
        4 * epsilon**2 * (Delta_r - omega) * B
        + gammaMM * A
        + 4 * epsilon**2 * kappaOpt * OmegaB**2
    )

    D = (
        gammaMM * (
            -2 * Delta_e * epsilon * kappaOpt
            + 2 * epsilon * (GammaOpt + kappaOpt) * omega
        )
        - 2 * epsilon * (Delta_r - omega) * A
        + 8 * epsilon**3 * omega * OmegaB**2
    )

    denom_real = (
        4 * Gmm**2 * epsilon**3
        * (Delta_e * kappaOpt - (GammaOpt + kappaOpt) * omega)
        + 2 * epsilon * (DeltaMM - omega) * C
        - kappaMM * D
    )

    denom_imag = (
        2 * Gmm**2 * epsilon**2 * A
        + kappaMM * C
        + 2 * epsilon * (DeltaMM - omega) * D
    )

    numerator = (
        64
        * Ein**2
        * Gopt**2
        * Gmm**2
        * epsilon**8
        * kappaOpt
        * kappaMM
        * OmegaB**2
    )

    denominator = denom_real**2 + denom_imag**2

    return numerator / denominator

def efficiency_plotter(
    omega_start,
    omega_end,
    omega_points,
    params,
    figsize=(7, 4.5),
    xlabel="780 nm Photon Cavity Detuning [MHz]",
    ylabel="Conversion Efficiency",
    plot_func=efficiency_func_OtoM,
):
    omega = np.linspace(omega_start, omega_end, omega_points)
    eta = plot_func(omega, **params)

    plt.figure(figsize=figsize)
    plt.plot(omega, eta)
    plt.fill_between(omega, eta, 0, alpha=0.25)

    plt.ylim(0, 1)
    plt.xlim(omega_start, omega_end)

    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)

    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    return plt.gcf(), plt.gca()