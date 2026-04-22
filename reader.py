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
        self.J = []       # current density mA/cm2

        self.parse()

    def parse(self):
        with open(self.path, 'r') as f:
            lines = f.readlines()

        # parse indicators and area
        for line in lines:
            line = line.strip()
            if line.startswith("Sample Area"):
                self.area = float(re.findall(r"[-+]?\d*\.\d+|\d+", line)[0])
            elif "Voc" in line:
                self.Voc = self.extract(line)
            elif "Jsc" in line:
                self.Jsc = self.extract(line)
            elif "Isc" in line:
                self.Isc = self.extract(line)
            elif "Fill Factor" in line:
                self.FF = self.extract(line)
            elif "Efficiency" in line:
                self.PCE = self.extract(line)
            elif "Rs" in line:
                self.Rs = self.extract(line)
            elif "Rsh" in line:
                self.Rsh = self.extract(line)

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