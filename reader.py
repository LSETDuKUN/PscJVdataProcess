import re

class DataFile:
    def __init__(self, path):
        self.path = path
        self.name = path.split("/")[-1]

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
        with open(self.path, 'r') as f:
            lines = f.readlines()

        # parse indicators and area
        for raw in lines:
            line = raw.strip()
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
            if "V(V)" in line and "I(mA)" in line and "P(mW)" in line:
                start = True
                continue
            if start:
                parts = line.strip().split()
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

