import csv
from pathlib import Path
import sys

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from helper_funcs import efficiency_func_OtoM, efficiency_func_MtoO, efficiency_func_2
import rabi_freq_HardCoded


EFFICIENCY_FUNCTIONS = {
    "OtoM": ("Optical to Microwave", efficiency_func_OtoM),
    "MtoO": ("Microwave to Optical", efficiency_func_MtoO),
    "func_2": ("Efficiency Function 2", efficiency_func_2),
}

RABI_CALCULATORS = {
    "arc": "ARC",
    "hardcoded": "Hard-coded dipoles",
}

INPUT_LABELS = {
    "gopt": "gopt (kHz)",
    "ModeVolumeOpt": "Optical mode volume (mm^3)",
    "gmm": "gmm (kHz)",
    "kappaOpt": "kappaOpt (MHz)",
    "kappaMM": "kappaMM (MHz)",
    "Natoms": "Natoms",
    "AtomRadius": "AtomRadius (um)",
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
        self.efficiency_combo = None
        self.rabi_combo = None
        self.gopt_source_combo = None
        self.gopt_result_label = QLabel()
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
                    ("ModeVolumeOpt", 0.083, 1e-9, 1e9, 0.001),
                    ("gmm", 91.0, 0.001, 1e6, 1.0),
                    ("kappaOpt", 10.0, 1e-6, 1e4, 0.1),
                    ("kappaMM", 10.0, 1e-6, 1e4, 0.1),
                    ("Delta_e", 0.0, -1e4, 1e4, 0.1),
                    ("Delta_r", 0.0, -1e4, 1e4, 0.1),
                    ("DeltaMM", 0.0, -1e4, 1e4, 0.1),
                ],
            )
        )
        layout.addWidget(self._make_optical_coupling_group())
        layout.addWidget(
            self._make_group(
                "Atom Parameters",
                [
                    ("Natoms", 5e5, 1.0, 1e10, 1e4),
                    ("AtomRadius", 250.0, 0.001, 1e6, 10.0),
                    ("gammaOpt", 6.0, 1e-6, 1e4, 0.1),
                    ("gammaMM", 100.0, 0.001, 1e7, 1.0),
                ],
            )
        )
        layout.addWidget(
            self._make_group(
                "Beam Parameters",
                [
                    ("PowerUV", 250.0, 0.001, 1e6, 10.0),
                    ("PowerBlue", 300.0, 0.001, 1e6, 10.0),
                    ("WaistUV", 1200.0, 0.001, 1e6, 10.0),
                    ("WaistBlue", 1000.0, 0.001, 1e6, 10.0),
                    ("DeltaUV", 2.0, 1e-6, 1e4, 0.1),
                    ("FBlue", 200.0, 1e-6, 1e6, 1.0),
                ],
            )
        )
        layout.addWidget(self._make_rabi_group())
        layout.addWidget(self._make_efficiency_group())
        layout.addWidget(self._make_actions_group())

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

    def _make_optical_coupling_group(self):
        group = QGroupBox("Optical Single-Atom g")
        form = QFormLayout(group)

        self.gopt_source_combo = QComboBox()
        self.gopt_source_combo.addItem("Manual gopt", "manual")
        self.gopt_source_combo.addItem("Calculate from mode volume", "mode_volume")
        self.gopt_source_combo.currentIndexChanged.connect(self.update_plot)
        form.addRow("Source", self.gopt_source_combo)
        form.addRow("g / 2pi", self.gopt_result_label)

        return group

    def _make_rabi_group(self):
        group = QGroupBox("Rabi Calculation")
        form = QFormLayout(group)

        self.rabi_combo = QComboBox()
        for key, label in RABI_CALCULATORS.items():
            self.rabi_combo.addItem(label, key)
        self.rabi_combo.currentIndexChanged.connect(self.update_plot)
        form.addRow("Source", self.rabi_combo)

        return group

    def _make_efficiency_group(self):
        group = QGroupBox("Efficiency Function")
        form = QFormLayout(group)

        self.efficiency_combo = QComboBox()
        for key, (label, _) in EFFICIENCY_FUNCTIONS.items():
            self.efficiency_combo.addItem(label, key)
        self.efficiency_combo.currentIndexChanged.connect(self.update_plot)
        form.addRow("Mode", self.efficiency_combo)

        return group

    def _make_actions_group(self):
        group = QGroupBox("Files")
        layout = QVBoxLayout(group)

        export_button = QPushButton("Export Parameters CSV")
        export_button.clicked.connect(self.export_parameters_csv)
        layout.addWidget(export_button)

        import_button = QPushButton("Import Parameters CSV")
        import_button.clicked.connect(self.import_parameters_csv)
        layout.addWidget(import_button)

        save_with_text_button = QPushButton("Save Graph With Textbox")
        save_with_text_button.clicked.connect(
            lambda: self.save_graph(show_stats=True)
        )
        layout.addWidget(save_with_text_button)

        save_without_text_button = QPushButton("Save Graph Without Textbox")
        save_without_text_button.clicked.connect(
            lambda: self.save_graph(show_stats=False)
        )
        layout.addWidget(save_without_text_button)

        save_all_button = QPushButton("Save All")
        save_all_button.clicked.connect(self.save_all)
        layout.addWidget(save_all_button)

        return group

    def values(self):
        return {name: spin_box.value() for name, spin_box in self.inputs.items()}

    def selected_efficiency_function(self):
        key = self.efficiency_combo.currentData()
        return EFFICIENCY_FUNCTIONS.get(key, EFFICIENCY_FUNCTIONS["OtoM"])[1]

    def selected_efficiency_label(self):
        key = self.efficiency_combo.currentData()
        return EFFICIENCY_FUNCTIONS.get(key, EFFICIENCY_FUNCTIONS["OtoM"])[0]

    def selected_rabi_calculator(self):
        key = self.rabi_combo.currentData()
        if key == "hardcoded":
            return rabi_freq_HardCoded.rabi_frequency_Rb85_fs

        from rabi_freq import rabi_frequency_Rb85_fs

        return rabi_frequency_Rb85_fs

    def _path_with_extension(self, file_path, selected_filter, fallback_extension):
        path = Path(file_path)
        if path.suffix:
            return str(path)

        filter_text = selected_filter.lower()
        for extension in (".png", ".pdf", ".svg", ".csv"):
            if extension[1:] in filter_text:
                return str(path.with_suffix(extension))

        return str(path.with_suffix(fallback_extension))

    def export_parameters_csv(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Parameters",
            "transduction_parameters.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        file_path = self._path_with_extension(file_path, selected_filter, ".csv")
        try:
            self._write_parameters_csv(file_path)
            self.status_label.setText(f"Exported parameters to {file_path}")
        except Exception as exc:
            self.status_label.setText(f"Parameter export failed: {exc}")

    def _write_parameters_csv(self, file_path):
        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["name", "label", "value"])
            writer.writeheader()
            for name, spin_box in self.inputs.items():
                writer.writerow(
                    {
                        "name": name,
                        "label": INPUT_LABELS.get(name, name),
                        "value": f"{spin_box.value():.12g}",
                    }
                )
            writer.writerow(
                {
                    "name": "gopt_source",
                    "label": "Optical g Calculation",
                    "value": self.gopt_source_combo.currentData(),
                }
            )
            writer.writerow(
                {
                    "name": "efficiency_function",
                    "label": "Efficiency Function",
                    "value": self.efficiency_combo.currentData(),
                }
            )
            writer.writerow(
                {
                    "name": "rabi_calculator",
                    "label": "Rabi Calculation",
                    "value": self.rabi_combo.currentData(),
                }
            )

    def import_parameters_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Parameters",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, newline="", encoding="utf-8-sig") as csv_file:
                reader = csv.DictReader(csv_file)
                updated_count = 0
                for row in reader:
                    name = (row.get("name") or row.get("parameter") or "").strip()
                    if name == "gopt_source":
                        value_text = (row.get("value") or "").strip()
                        index = self.gopt_source_combo.findData(value_text)
                        if index >= 0:
                            self.gopt_source_combo.blockSignals(True)
                            self.gopt_source_combo.setCurrentIndex(index)
                            self.gopt_source_combo.blockSignals(False)
                            updated_count += 1
                        continue
                    if name == "efficiency_function":
                        value_text = (row.get("value") or "").strip()
                        index = self.efficiency_combo.findData(value_text)
                        if index >= 0:
                            self.efficiency_combo.blockSignals(True)
                            self.efficiency_combo.setCurrentIndex(index)
                            self.efficiency_combo.blockSignals(False)
                            updated_count += 1
                        continue
                    if name == "rabi_calculator":
                        value_text = (row.get("value") or "").strip()
                        index = self.rabi_combo.findData(value_text)
                        if index >= 0:
                            self.rabi_combo.blockSignals(True)
                            self.rabi_combo.setCurrentIndex(index)
                            self.rabi_combo.blockSignals(False)
                            updated_count += 1
                        continue

                    if name not in self.inputs:
                        continue

                    value_text = (row.get("value") or "").strip()
                    if not value_text:
                        continue

                    spin_box = self.inputs[name]
                    spin_box.blockSignals(True)
                    spin_box.setValue(float(value_text))
                    spin_box.blockSignals(False)
                    updated_count += 1

            self.update_plot()
            self.status_label.setText(
                f"Imported {updated_count} parameters from {file_path}"
            )
        except Exception as exc:
            if self.efficiency_combo is not None:
                self.efficiency_combo.blockSignals(False)
            if self.rabi_combo is not None:
                self.rabi_combo.blockSignals(False)
            if self.gopt_source_combo is not None:
                self.gopt_source_combo.blockSignals(False)
            for spin_box in self.inputs.values():
                spin_box.blockSignals(False)
            self.status_label.setText(f"Parameter import failed: {exc}")

    def optical_single_atom_g_khz(self, values):
        if self.gopt_source_combo.currentData() == "mode_volume":
            mode_volume_m3 = values["ModeVolumeOpt"] * 1e-9
            return rabi_freq_HardCoded.single_atom_g_optical(mode_volume_m3)[
                "g_kHz"
            ]
        return values["gopt"]

    def calculate_params(self):
        values = self.values()
        gopt_mhz = self.optical_single_atom_g_khz(values) * 1e-3
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
        rabi_frequency_Rb85_fs = self.selected_rabi_calculator()

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

    def _calculate_fwhm(self, omega, eta, peak_index):
        half_max = eta[peak_index] / 2.0

        def crossing_between(first_index, second_index):
            x0 = omega[first_index]
            x1 = omega[second_index]
            y0 = eta[first_index]
            y1 = eta[second_index]
            if y1 == y0:
                return x0
            return x0 + (half_max - y0) * (x1 - x0) / (y1 - y0)

        left_index = peak_index
        while left_index > 0 and eta[left_index] >= half_max:
            left_index -= 1

        if left_index == 0 and eta[left_index] >= half_max:
            left_crossing = omega[0]
        else:
            left_crossing = crossing_between(left_index, left_index + 1)

        right_index = peak_index
        last_index = len(eta) - 1
        while right_index < last_index and eta[right_index] >= half_max:
            right_index += 1

        if right_index == last_index and eta[right_index] >= half_max:
            right_crossing = omega[-1]
        else:
            right_crossing = crossing_between(right_index - 1, right_index)

        return right_crossing - left_crossing

    def _calculate_plot_data(self):
        params = self.calculate_params()
        omega = np.linspace(-10.0, 10.0, 1000)
        eta = self.selected_efficiency_function()(omega, **params)
        peak_index = int(np.nanargmax(eta))
        max_eff = eta[peak_index] * 100.0
        fwhm = self._calculate_fwhm(omega, eta, peak_index)
        return omega, eta, max_eff, fwhm

    def _draw_efficiency_plot(self, ax, omega, eta, max_eff, fwhm, show_stats):
        ax.clear()
        ax.plot(omega, eta)
        ax.fill_between(omega, eta, 0, alpha=0.25)
        if show_stats:
            ax.text(
                0.03,
                0.95,
                f"Maximum Efficiency = {max_eff:.3f}%\nBandwidth = {fwhm:.3f} MHz",
                transform=ax.transAxes,
                ha="left",
                va="top",
                bbox={
                    "boxstyle": "round,pad=0.35",
                    "facecolor": "white",
                    "edgecolor": "0.75",
                    "alpha": 0.85,
                },
            )
        ax.set_ylim(0, 1)
        ax.set_xlim(-10, 10)
        ax.set_xlabel("Photon Cavity Detuning [MHz]", fontsize=14)
        ax.set_ylabel("Conversion Efficiency", fontsize=14)
        ax.set_title(self.selected_efficiency_label(), fontsize=14)
        ax.grid(True, alpha=0.3)

    def save_graph(self, show_stats):
        suffix = "with_textbox" if show_stats else "without_textbox"
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Graph",
            f"transduction_efficiency_{suffix}.png",
            "PNG Images (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)",
        )
        if not file_path:
            return

        file_path = self._path_with_extension(file_path, selected_filter, ".png")
        try:
            self._save_graph_file(file_path, show_stats)
            self.status_label.setText(f"Saved graph to {file_path}")
        except Exception as exc:
            self.status_label.setText(f"Graph save failed: {exc}")

    def _save_graph_file(self, file_path, show_stats, plot_data=None):
        if plot_data is None:
            plot_data = self._calculate_plot_data()

        omega, eta, max_eff, fwhm = plot_data
        figure = Figure(figsize=(7, 4.5))
        ax = figure.add_subplot(111)
        self._draw_efficiency_plot(ax, omega, eta, max_eff, fwhm, show_stats)
        figure.tight_layout()
        figure.savefig(file_path, dpi=300)

    def save_all(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save All",
            "transduction_efficiency.png",
            "PNG Images (*.png);;All Files (*)",
        )
        if not file_path:
            return

        plot_path = Path(
            self._path_with_extension(file_path, selected_filter, ".png")
        )
        base_path = plot_path.with_suffix("")

        plot_no_legend_path = base_path.with_name(
            f"{base_path.name}_noLegend"
        ).with_suffix(".png")
        params_path = base_path.with_name(f"{base_path.name}_params").with_suffix(
            ".csv"
        )

        try:
            plot_data = self._calculate_plot_data()
            self._save_graph_file(plot_path, show_stats=True, plot_data=plot_data)
            self._save_graph_file(
                plot_no_legend_path,
                show_stats=False,
                plot_data=plot_data,
            )
            self._write_parameters_csv(params_path)
            self.status_label.setText(
                "Saved all files: "
                f"{plot_path}, {plot_no_legend_path}, {params_path}"
            )
        except Exception as exc:
            self.status_label.setText(f"Save all failed: {exc}")

    def update_plot(self):
        try:
            gopt_khz = self.optical_single_atom_g_khz(self.values())
            self.gopt_result_label.setText(f"{gopt_khz:.6g} kHz")
            omega, eta, max_eff, fwhm = self._calculate_plot_data()
            self._draw_efficiency_plot(self.ax, omega, eta, max_eff, fwhm, True)
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
