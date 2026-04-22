import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QListWidget, QLineEdit, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QSplitter
)
from PyQt5.QtCore import Qt

from reader import DataFile
from filter_sort import filter_files, sort_files
from plotter import plot_files


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solar Data Analyzer")

        self.files = []
        self.filtered = []
        self.effective = []
        self.uneffective = []

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # load
        self.load_btn = QPushButton("Load Folder")
        self.load_btn.clicked.connect(self.load_folder)
        left_layout.addWidget(self.load_btn)

        # filters
        f_layout = QHBoxLayout()

        self.pce = QLineEdit(); self.pce.setPlaceholderText("PCE")
        self.voc = QLineEdit(); self.voc.setPlaceholderText("Voc")
        self.jsc = QLineEdit(); self.jsc.setPlaceholderText("Jsc")
        self.ff = QLineEdit(); self.ff.setPlaceholderText("FF")

        self.logic_box = QComboBox()
        self.logic_box.addItems(["AND", "OR"])

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.clicked.connect(self.apply_filter)

        for w in [self.pce, self.voc, self.jsc, self.ff, self.logic_box, self.filter_btn]:
            f_layout.addWidget(w)

        left_layout.addLayout(f_layout)

        # lists
        lists_layout = QHBoxLayout()

        v_eff_layout = QVBoxLayout()
        v_eff_layout.addWidget(QLabel("Effective"))
        self.list_widget_eff = QListWidget()
        self.list_widget_eff.itemSelectionChanged.connect(self.selection_changed)
        v_eff_layout.addWidget(self.list_widget_eff)

        v_uneff_layout = QVBoxLayout()
        v_uneff_layout.addWidget(QLabel("Uneffective"))
        self.list_widget_uneff = QListWidget()
        self.list_widget_uneff.itemSelectionChanged.connect(self.selection_changed)
        v_uneff_layout.addWidget(self.list_widget_uneff)

        lists_layout.addLayout(v_eff_layout)
        lists_layout.addLayout(v_uneff_layout)

        left_layout.addLayout(lists_layout)

        # plot settings
        plot_layout = QHBoxLayout()
        self.xmin = QLineEdit(); self.xmin.setPlaceholderText("X min")
        self.xmax = QLineEdit(); self.xmax.setPlaceholderText("X max")
        self.ymin = QLineEdit(); self.ymin.setPlaceholderText("Y min")
        self.ymax = QLineEdit(); self.ymax.setPlaceholderText("Y max")
        for w in [self.xmin, self.xmax, self.ymin, self.ymax]:
            plot_layout.addWidget(w)

        # plot
        self.plot_btn = QPushButton("Plot")
        self.plot_btn.clicked.connect(self.plot_selected)
        plot_layout.addWidget(self.plot_btn)
        left_layout.addLayout(plot_layout)

        # Table for data
        right_layout.addWidget(QLabel("Data Table"))
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["V(V)", "I(mA)", "P(mW)", "J(mA/cm2)"])
        right_layout.addWidget(self.table)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.files.clear()

        for file in os.listdir(folder):
            if file.endswith(".txt"):
                path = os.path.join(folder, file)
                self.files.append(DataFile(path))

        self.files = sort_files(self.files, "PCE")
        self.effective = self.files
        self.uneffective = []
        self.update_lists()

    def apply_filter(self):
        min_pce = float(self.pce.text() or 0)
        min_voc = float(self.voc.text() or 0)
        min_jsc = float(self.jsc.text() or 0)
        min_ff = float(self.ff.text() or 0)
        logic = self.logic_box.currentText()

        self.effective, self.uneffective = filter_files(
            self.files, min_pce, min_voc, min_jsc, min_ff, logic
        )

        self.effective = sort_files(self.effective, "PCE")
        self.uneffective = sort_files(self.uneffective, "PCE")

        self.update_lists()

    def update_lists(self):
        self.list_widget_eff.clear()
        for f in self.effective:
            self.list_widget_eff.addItem(f"{f.name} | PCE={f.PCE if f.PCE else 0:.2f}")

        self.list_widget_uneff.clear()
        for f in self.uneffective:
            self.list_widget_uneff.addItem(f"{f.name} | PCE={f.PCE if f.PCE else 0:.2f}")

    def selection_changed(self):
        sender = self.sender()
        selected = sender.selectedItems()
        if not selected:
            return

        # clear selection of the other list
        if sender == self.list_widget_eff:
            self.list_widget_uneff.clearSelection()
            source = self.effective
        else:
            self.list_widget_eff.clearSelection()
            source = self.uneffective

        name = selected[0].text().split("|")[0].strip()
        selected_file = None
        for f in source:
            if f.name == name:
                selected_file = f
                break

        if selected_file:
            self.update_table(selected_file)

    def update_table(self, file_data):
        self.table.setRowCount(len(file_data.data))
        for row, ((v, i, p), j) in enumerate(zip(file_data.data, file_data.J)):
            self.table.setItem(row, 0, QTableWidgetItem(f"{v:.4f}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{i:.4f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{p:.4f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{j:.4f}"))

    def plot_selected(self):
        selected = self.list_widget_eff.selectedItems() + self.list_widget_uneff.selectedItems()
        if not selected:
            return

        selected_files = []
        source = self.effective + self.uneffective

        for item in selected:
            name = item.text().split("|")[0].strip()
            for f in source:
                if f.name == name:
                    selected_files.append(f)

        def try_float(text):
            try: return float(text)
            except: return None

        xlim = (try_float(self.xmin.text()), try_float(self.xmax.text()))
        ylim = (try_float(self.ymin.text()), try_float(self.ymax.text()))

        plot_files(selected_files, xlim=xlim, ylim=ylim)
