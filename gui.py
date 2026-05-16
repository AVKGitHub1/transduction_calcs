import sys

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from helper_funcs import efficiency_func
from rabi_freq import rabi_frequency_Rb85_fs


INPUT_LABELS = {
    "gopt": "gopt (kHz)",
    "gmm": "gmm (kHz)",
    "kappaOpt": "kappaOpt (MHz)",
    "kappaMM": "kappaMM (MHz)",
    "Natoms": "Natoms",
    "AtomRadius": "AtomRadius (m)",
    "gammaOpt": "gammaOpt (MHz)",
    "gammaMM": "gammaMM (kHz)",
    "PowerUV": "PowerUV (mW)",
    "PowerBlue": "PowerBlue (mW)",
    "WaistUV": "WaistUV (um)",
    "WaistBlue": "WaistBlue (um)",
    "DeltaUV": "DeltaUV (MHz)",
    "FBlue": "FBlue",
    "Delta_e": "Delta_e (MHz)",
    "Delta_r": "Delta_r (MHz)",
    "DeltaMM": "DeltaMM (MHz)",
}


class ScientificDoubleSpinBox(QDoubleSpinBox):
    def textFromValue(self, value):
        if value != 0 and (abs(value) < 1e-3 or abs(value) >= 1e4):
            return f"{value:.6g}"
        return f"{value:.6f}".rstrip("0").rstrip(".")


class TransductionGui(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Transduction GUI")
        self.inputs = {}
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)

        self.figure = Figure(figsize=(7, 4.5))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.ax = self.figure.add_subplot(111)

        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.addWidget(self._build_controls(), stretch=0)

        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.canvas, stretch=1)
        plot_layout.addWidget(self.status_label)
        root_layout.addLayout(plot_layout, stretch=1)

        self.setCentralWidget(central)
        self.resize(1100, 650)
        self.update_plot()

    def _build_controls(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(
            self._make_group(
                "Cavity Parameters",
                [
                    ("gopt", 25.0, 0.001, 1e6, 1.0),
                    ("gmm", 91.0, 0.001, 1e6, 1.0),
                    ("kappaOpt", 10.0, 1e-6, 1e4, 0.1),
                    ("kappaMM", 10.0, 1e-6, 1e4, 0.1),
                    ("Delta_e", 0.0, -1e4, 1e4, 0.1),
                    ("Delta_r", 0.0, -1e4, 1e4, 0.1),
                    ("DeltaMM", 0.0, -1e4, 1e4, 0.1),
                ],
            )
        )
        layout.addWidget(
            self._make_group(
                "Atom Parameters",
                [
                    ("Natoms", 5e5, 1.0, 1e10, 1e4),
                    ("AtomRadius", 250e-6, 1e-9, 1.0, 10e-6),
                    ("gammaOpt", 6.0, 1e-6, 1e4, 0.1),
                    ("gammaMM", 100.0, 0.001, 1e7, 1.0),
                ],
            )
        )
        layout.addWidget(
            self._make_group(
                "Beam Parameters",
                [
                    ("PowerUV", 200.0, 0.001, 1e6, 10.0),
                    ("PowerBlue", 200.0, 0.001, 1e6, 10.0),
                    ("WaistUV", 1200.0, 0.001, 1e6, 10.0),
                    ("WaistBlue", 1200.0, 0.001, 1e6, 10.0),
                    ("DeltaUV", 5.0, 1e-6, 1e4, 0.1),
                    ("FBlue", 100.0, 1e-6, 1e6, 1.0),
                ],
            )
        )

        return panel

    def _make_group(self, title, fields):
        group = QGroupBox(title)
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        for name, default, minimum, maximum, step in fields:
            spin_box = ScientificDoubleSpinBox()
            spin_box.setDecimals(9)
            spin_box.setRange(minimum, maximum)
            spin_box.setSingleStep(step)
            spin_box.setValue(default)
            spin_box.valueChanged.connect(self.update_plot)
            self.inputs[name] = spin_box
            form.addRow(INPUT_LABELS.get(name, name), spin_box)

        return group

    def values(self):
        return {name: spin_box.value() for name, spin_box in self.inputs.items()}

    def calculate_params(self):
        values = self.values()
        gopt_mhz = values["gopt"] * 1e-3
        gmm_mhz = values["gmm"] * 1e-3
        gamma_mm_mhz = values["gammaMM"] * 1e-3
        power_uv_w = values["PowerUV"] * 1e-3
        power_blue_w = values["PowerBlue"] * 1e-3
        waist_uv_m = values["WaistUV"] * 1e-6
        waist_blue_m = values["WaistBlue"] * 1e-6

        ground_state = (5, 0, 0.5, 0.5)
        excited_state = (5, 1, 1.5, 1.5)
        rydberg_r_state = (55, 0, 0.5)
        rydberg_f_state = (54, 1, 1.5)

        omega_blue = rabi_frequency_Rb85_fs(
            excited_state,
            rydberg_r_state,
            -1,
            power_blue_w,
            waist_blue_m,
        )["Omega_MHz"]
        omega_uv = rabi_frequency_Rb85_fs(
            ground_state,
            rydberg_f_state,
            1,
            power_uv_w,
            waist_uv_m,
        )["Omega_MHz"]

        theta_uv = np.arctan(abs(omega_uv / values["DeltaUV"]))
        n_mm = values["Natoms"] * np.sin(theta_uv) ** 2
        n_opt = values["Natoms"] * np.cos(theta_uv) ** 2

        return {
            "Gopt": gopt_mhz * np.sqrt(n_opt),
            "Gmm": gmm_mhz * np.sqrt(n_mm),
            "kappaOpt": values["kappaOpt"],
            "GammaOpt": values["gammaOpt"],
            "Delta_e": values["Delta_e"],
            "Delta_r": values["Delta_r"],
            "gammaMM": gamma_mm_mhz,
            "kappaMM": values["kappaMM"],
            "DeltaMM": values["DeltaMM"],
            "OmegaB": np.sqrt(values["FBlue"] / np.pi) * omega_blue,
            "Ein": 1.0,
            "epsilon": 1.0,
        }

    def update_plot(self):
        try:
            params = self.calculate_params()
            omega = np.linspace(-10.0, 10.0, 1000)
            eta = efficiency_func(omega, **params)

            self.ax.clear()
            self.ax.plot(omega, eta)
            self.ax.fill_between(omega, eta, 0, alpha=0.25)
            self.ax.set_ylim(0, 1)
            self.ax.set_xlim(-10, 10)
            self.ax.set_xlabel("780 nm Photon Cavity Detuning [MHz]", fontsize=14)
            self.ax.set_ylabel("Conversion Efficiency", fontsize=14)
            self.ax.grid(True, alpha=0.3)
            self.figure.tight_layout()
            self.status_label.setText("")
        except Exception as exc:
            self.status_label.setText(f"Plot update failed: {exc}")
        finally:
            self.canvas.draw_idle()


def main():
    app = QApplication(sys.argv)
    window = TransductionGui()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
