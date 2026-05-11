import re
import os

class DataFile:
    def __init__(self, path):
        self.path = path
        # 兼容 Windows 路径分隔符
        self.name = os.path.basename(path)

        # indicators
        self.Voc = None
        self.Jsc = None
        self.Isc = None
        self.FF = None
        self.PCE = None
        self.Rs = None
        self.Rsh = None

        self.area = None  # in cm^2
        self.data = []    # list of tuples: (V, I, P)
        self.data_str = [] # raw string data to preserve exact representation
        self.J = []       # current density mA/cm2

        self.parse()

    def _extract_by_key(self, line: str, key: str):
        """Extract numeric value from a 'key: value' / 'key = value' style line.

        This avoids accidentally capturing unrelated numbers on the same line.
        """
        # Example matches:
        #   Jsc: 22.1
        #   Jsc (mA/cm2) = 22.1
        #   Voc	0.98
        pattern = rf"\b{re.escape(key)}\b\s*(?:\([^)]*\))?\s*[:=\t ]\s*([-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?)"
        m = re.search(pattern, line, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                return None
        return None

    def parse(self):
        ext = os.path.splitext(self.path)[1].lower()
        if ext in (".xls", ".xlsx"):
            lines = self._read_excel_as_lines()
        else:
            with open(self.path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

        # parse indicators and area
        for raw in lines:
            line = str(raw).strip()
            if not line:
                continue

            if line.lower().startswith("sample area"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    match = re.findall(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|\d+", parts[1])
                    if match:
                        self.area = float(match[0])
                continue

            # Skip potential table header lines
            if "v(v)" in line.lower() and "i(ma)" in line.lower() and "p(mw)" in line.lower():
                continue

            # Prefer strict key-based extraction to avoid mis-parsing
            val = self._extract_by_key(line, "Voc")
            if val is not None:
                self.Voc = val
                continue

            val = self._extract_by_key(line, "Jsc")
            if val is not None:
                self.Jsc = val
                continue

            val = self._extract_by_key(line, "Isc")
            if val is not None:
                self.Isc = val
                continue

            if "fill factor" in line.lower():
                self.FF = self.extract(line)
                continue

            if "efficiency" in line.lower():
                self.PCE = self.extract(line)
                continue

            # Avoid matching Rs/Rsh inside other words
            val = self._extract_by_key(line, "Rs")
            if val is not None:
                self.Rs = val
                continue

            val = self._extract_by_key(line, "Rsh")
            if val is not None:
                self.Rsh = val
                continue

        # parse V-I-P table
        start = False
        for line in lines:
            line = str(line)
            if "V(V)" in line and "I(mA)" in line and "P(mW)" in line:
                start = True
                continue
            if start:
                parts = str(line).strip().split()
                if len(parts) == 3:
                    try:
                        v, i, p = map(float, parts)
                        self.data.append((v, i, p))
                        self.data_str.append((parts[0], parts[1], parts[2]))
                        # calculate current density
                        if self.area and self.area > 0:
                            self.J.append(i / self.area)
                        else:
                            self.J.append(i)  # fallback
                    except:
                        continue

    def extract(self, line):
        match = re.findall(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|\d+", line)
        if match:
            return float(match[0])
        return None

    def _read_excel_as_lines(self):
        """把 Excel 的内容转换成与 txt 近似的行列表（字符串），以复用现有解析逻辑。"""
        try:
            import pandas as pd
        except Exception as e:
            raise RuntimeError("读取 Excel 需要安装 pandas") from e

        # pandas 读取 .xlsx 依赖 openpyxl；.xls 一般需要 xlrd。
        try:
            df = pd.read_excel(self.path, header=None, engine=None)
        except Exception:
            # 给出更明确的错误信息（避免静默失败）
            ext = os.path.splitext(self.path)[1].lower()
            if ext == ".xlsx":
                raise RuntimeError("读取 .xlsx 失败：请确认已安装 openpyxl")
            if ext == ".xls":
                raise RuntimeError("读取 .xls 失败：建议将文件另存为 .xlsx，或安装 xlrd(<=1.2) 后再试")
            raise

        lines = []
        for _, row in df.iterrows():
            vals = []
            for v in row.tolist():
                if v is None:
                    continue
                # pandas/numpy NaN
                try:
                    if pd.isna(v):
                        continue
                except Exception:
                    pass
                s = str(v).strip()
                if s != "":
                    vals.append(s)
            if not vals:
                continue

            # 单列：保留为一行文本（用于诸如 "Sample area: ..." / "Voc ..." 等指标行）
            if len(vals) == 1:
                lines.append(vals[0] + "\n")
            else:
                # 多列：用空格拼接，匹配原先的 split() 行为（例如 V I P 三列）
                lines.append(" ".join(vals) + "\n")

        return lines
