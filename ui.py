import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QSplitter,
    QAbstractItemView, QApplication
)
from PyQt5.QtGui import QColor

from reader import DataFile
from filter_sort import filter_files, sort_files

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Solar Data Analyzer")

        self.files = []
        self.effective = []
        self.uneffective = []
        self._folder_colors = {}
        self._palette = [
            QColor("#E3F2FD"), QColor("#E8F5E9"), QColor("#FFF3E0"), QColor("#F3E5F5"),
            QColor("#FFEBEE"), QColor("#E0F7FA"), QColor("#F9FBE7"), QColor("#EFEBE9")
        ]

        main_layout = QHBoxLayout()

        splitter = QSplitter()

        # ---- Left panel ----
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # load controls
        load_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Folder")
        self.load_btn.clicked.connect(self.load_folder)
        self.load_btn.setStyleSheet("padding: 6px;")

        self.load_root_btn = QPushButton("Load Root Folder")
        self.load_root_btn.clicked.connect(self.load_root_folder)
        self.load_root_btn.setStyleSheet("padding: 6px;")

        load_layout.addWidget(self.load_btn)
        load_layout.addWidget(self.load_root_btn)
        left_layout.addLayout(load_layout)

        # filters
        f_layout = QHBoxLayout()

        self.pce = QLineEdit(); self.pce.setPlaceholderText("min PCE")
        self.logic1 = QComboBox(); self.logic1.addItems(["AND", "OR"])
        self.voc = QLineEdit(); self.voc.setPlaceholderText("min Voc")
        self.logic2 = QComboBox(); self.logic2.addItems(["AND", "OR"])
        self.jsc = QLineEdit(); self.jsc.setPlaceholderText("min Jsc")
        self.logic3 = QComboBox(); self.logic3.addItems(["AND", "OR"])
        self.ff = QLineEdit(); self.ff.setPlaceholderText("min FF")

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.clicked.connect(self.apply_filter)
        self.filter_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")

        for w in [self.pce, self.logic1, self.voc, self.logic2, self.jsc, self.logic3, self.ff, self.filter_btn]:
            f_layout.addWidget(w)

        left_layout.addLayout(f_layout)

        # file tables
        tbls_layout = QHBoxLayout()

        eff_layout = QVBoxLayout()
        lbl_eff = QLabel("Effective")
        lbl_eff.setStyleSheet("font-weight: bold; color: #2E7D32;")
        eff_layout.addWidget(lbl_eff)
        self.table_eff = QTableWidget()
        self._init_file_table(self.table_eff)
        self.table_eff.itemSelectionChanged.connect(self.selection_changed)
        eff_layout.addWidget(self.table_eff)

        uneff_layout = QVBoxLayout()
        lbl_uneff = QLabel("Uneffective")
        lbl_uneff.setStyleSheet("font-weight: bold; color: #C62828;")
        uneff_layout.addWidget(lbl_uneff)
        self.table_uneff = QTableWidget()
        self._init_file_table(self.table_uneff)
        self.table_uneff.itemSelectionChanged.connect(self.selection_changed)
        uneff_layout.addWidget(self.table_uneff)

        tbls_layout.addLayout(eff_layout)
        tbls_layout.addLayout(uneff_layout)
        left_layout.addLayout(tbls_layout)

        # plot settings + button
        plot_ctl_layout = QHBoxLayout()
        self.xmin = QLineEdit(); self.xmin.setPlaceholderText("X min")
        self.xmax = QLineEdit(); self.xmax.setPlaceholderText("X max")
        self.ymin = QLineEdit(); self.ymin.setPlaceholderText("Y min")
        self.ymax = QLineEdit(); self.ymax.setPlaceholderText("Y max")
        for w in [self.xmin, self.xmax, self.ymin, self.ymax]:
            plot_ctl_layout.addWidget(w)

        self.plot_btn = QPushButton("Plot")
        self.plot_btn.clicked.connect(self.plot_selected)
        plot_ctl_layout.addWidget(self.plot_btn)

        self.auto_plot = QComboBox()
        self.auto_plot.addItems(["Auto Plot: ON", "Auto Plot: OFF"])
        plot_ctl_layout.addWidget(self.auto_plot)

        left_layout.addLayout(plot_ctl_layout)

        # embedded plot
        self.canvas = MplCanvas(self)
        left_layout.addWidget(self.canvas)

        splitter.addWidget(left_panel)

        # ---- Right panel ----
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        data_hdr = QHBoxLayout()
        data_hdr.addWidget(QLabel("Data Table"))
        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_selected_btn.clicked.connect(self.copy_selected)
        self.copy_col_btn = QPushButton("Copy Column")
        self.copy_col_btn.clicked.connect(self.copy_column)
        data_hdr.addWidget(self.copy_selected_btn)
        data_hdr.addWidget(self.copy_col_btn)
        data_hdr.addStretch(1)
        right_layout.addLayout(data_hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["V(V)", "J(mA/cm2)", "I(mA)", "P(mW)"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        right_layout.addWidget(self.table)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def _init_file_table(self, table: QTableWidget):
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Folder", "File", "PCE", "FF", "Jsc", "Voc"])
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)

    def _color_for_folder(self, folder: str):
        if folder not in self._folder_colors:
            idx = len(self._folder_colors) % len(self._palette)
            self._folder_colors[folder] = self._palette[idx]
        return self._folder_colors[folder]

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        self._load_from_folder(folder, recursive=False)

    def load_root_folder(self):
        root = QFileDialog.getExistingDirectory(self, "Select Root Folder")
        if not root:
            return
        self._load_from_folder(root, recursive=True)

    def _load_from_folder(self, folder: str, recursive: bool):
        self.files.clear()
        self._folder_colors.clear()

        if recursive:
            for dirpath, _, filenames in os.walk(folder):
                for fn in filenames:
                    if fn.endswith(".txt"):
                        path = os.path.join(dirpath, fn)
                        df = DataFile(path)
                        df.folder = os.path.relpath(dirpath, folder)
                        self.files.append(df)
        else:
            for fn in os.listdir(folder):
                if fn.endswith(".txt"):
                    path = os.path.join(folder, fn)
                    df = DataFile(path)
                    df.folder = os.path.basename(folder)
                    self.files.append(df)

        self.files = sort_files(self.files, "PCE")
        self.effective = self.files
        self.uneffective = []
        self.update_file_tables()

    def apply_filter(self):
        min_pce = float(self.pce.text() or 0)
        min_voc = float(self.voc.text() or 0)
        min_jsc = float(self.jsc.text() or 0)
        min_ff = float(self.ff.text() or 0)
        logic = (self.logic1.currentText(), self.logic2.currentText(), self.logic3.currentText())

        self.effective, self.uneffective = filter_files(
            self.files, min_pce, min_voc, min_jsc, min_ff, logic
        )

        self.effective = sort_files(self.effective, "PCE")
        self.uneffective = sort_files(self.uneffective, "PCE")

        self.update_file_tables()

    def update_file_tables(self):
        self._fill_file_table(self.table_eff, self.effective)
        self._fill_file_table(self.table_uneff, self.uneffective)

    def _fmt(self, v, prec=3):
        if v is None:
            return ""
        try:
            return f"{float(v):.{prec}f}"
        except Exception:
            return str(v)

    def _fill_file_table(self, table: QTableWidget, files):
        table.setRowCount(len(files))
        for r, f in enumerate(files):
            folder = getattr(f, "folder", "")
            table.setItem(r, 0, QTableWidgetItem(folder))
            table.setItem(r, 1, QTableWidgetItem(f.name))
            table.setItem(r, 2, QTableWidgetItem(self._fmt(f.PCE, 3)))
            table.setItem(r, 3, QTableWidgetItem(self._fmt(f.FF, 3)))
            table.setItem(r, 4, QTableWidgetItem(self._fmt(f.Jsc, 3)))
            table.setItem(r, 5, QTableWidgetItem(self._fmt(f.Voc, 3)))

            # color rows by folder
            bg = self._color_for_folder(folder)
            for c in range(table.columnCount()):
                it = table.item(r, c)
                if it is not None:
                    it.setBackground(bg)

    def update_table(self, file_data: DataFile):
        """Fill the right-side data table."""
        if not hasattr(file_data, "data_str"):
            return

        self.table.setRowCount(len(file_data.data_str))
        for row, ((v_str, i_str, p_str), j) in enumerate(zip(file_data.data_str, file_data.J)):
            self.table.setItem(row, 0, QTableWidgetItem(v_str))
            self.table.setItem(row, 1, QTableWidgetItem(f"{j:.6E}" if j is not None else ""))
            self.table.setItem(row, 2, QTableWidgetItem(i_str))
            self.table.setItem(row, 3, QTableWidgetItem(p_str))

    def selection_changed(self):
        sender = self.sender()
        if sender not in (self.table_eff, self.table_uneff):
            return

        # keep single selection across two tables
        if sender == self.table_eff:
            self.table_uneff.clearSelection()
            files = self.effective
        else:
            self.table_eff.clearSelection()
            files = self.uneffective

        sel = sender.selectionModel().selectedRows()
        if not sel:
            return

        row = sel[0].row()
        if row < 0 or row >= len(files):
            return

        f = files[row]
        self.update_table(f)

        if self.auto_plot.currentText().endswith("ON"):
            def try_float(text):
                try:
                    return float(text)
                except Exception:
                    return None
            xlim = (try_float(self.xmin.text()), try_float(self.xmax.text()))
            ylim = (try_float(self.ymin.text()), try_float(self.ymax.text()))
            self._plot_on_canvas([f], xlim=xlim, ylim=ylim)

    def copy_selected(self):
        items = self.table.selectedItems()
        if not items:
            return

        # build TSV according to selection rectangle(s)
        rows = sorted({it.row() for it in items})
        cols = sorted({it.column() for it in items})

        grid = []
        for r in rows:
            line = []
            for c in cols:
                it = self.table.item(r, c)
                line.append(it.text() if it else "")
            grid.append("\t".join(line))

        QApplication.clipboard().setText("\n".join(grid))

    def copy_column(self):
        cols = sorted({it.column() for it in self.table.selectedItems()})
        if not cols:
            return

        # if user selected multiple columns, copy them all
        out_lines = []
        for r in range(self.table.rowCount()):
            line = []
            for c in cols:
                it = self.table.item(r, c)
                line.append(it.text() if it else "")
            out_lines.append("\t".join(line))

        QApplication.clipboard().setText("\n".join(out_lines))

    def plot_selected(self):
        selected = []

        sel_eff = self.table_eff.selectionModel().selectedRows()
        if sel_eff:
            selected.append(self.effective[sel_eff[0].row()])

        sel_uneff = self.table_uneff.selectionModel().selectedRows()
        if sel_uneff:
            selected.append(self.uneffective[sel_uneff[0].row()])

        if not selected:
            return

        def try_float(text):
            try:
                return float(text)
            except Exception:
                return None

        xlim = (try_float(self.xmin.text()), try_float(self.xmax.text()))
        ylim = (try_float(self.ymin.text()), try_float(self.ymax.text()))

        self._plot_on_canvas(selected, xlim=xlim, ylim=ylim)

    def _plot_on_canvas(self, files, xlim=None, ylim=None):
        ax = self.canvas.ax
        ax.clear()

        # Origin-like styling
        ax.tick_params(direction='in', length=6, width=1.5, colors='k',
                       bottom=True, top=True, left=True, right=True)
        for spine in ax.spines.values():
            spine.set_linewidth(1.5)

        for f in files:
            if not f.data:
                continue
            V = [x[0] for x in f.data]
            J = f.J
            ax.plot(V, J, marker='o', linestyle='-', linewidth=2, markersize=4, label=f.name)

        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("Current Density (mA/cm²)")
        ax.set_title("J-V Curves")

        if xlim and xlim[0] is not None and xlim[1] is not None:
            ax.set_xlim(xlim)
        if ylim and ylim[0] is not None and ylim[1] is not None:
            ax.set_ylim(ylim)

        ax.legend(frameon=False, fontsize=9)
        self.canvas.fig.tight_layout()
        self.canvas.draw()
