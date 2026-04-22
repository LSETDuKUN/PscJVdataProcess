import matplotlib.pyplot as plt

def plot_files(files, plot_power=False, xlim=None, ylim=None):
    plt.figure(figsize=(8,6))
    ax = plt.gca()

    # Origin style
    plt.rcParams['font.family'] = 'Arial'
    ax.tick_params(direction='in', length=6, width=1.5, colors='k',
                   grid_color='k', grid_alpha=0.5, bottom=True, top=True, left=True, right=True)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    for f in files:
        if not f.data:
            continue

        V = [x[0] for x in f.data]
        J = f.J  # mA/cm2

        # Plot current density with markers + line
        plt.plot(V, J, marker='o', linestyle='-', linewidth=2, markersize=5, label=f"{f.name} (J)")

        # Optional: plot power curve
        if plot_power:
            P = [x[2] for x in f.data]
            plt.plot(V, P, marker='s', linestyle='--', linewidth=1.5, markersize=4, label=f"{f.name} (P)")

    plt.xlabel("Voltage (V)", fontsize=14, fontweight='bold')
    plt.ylabel("Current Density (mA/cm²)", fontsize=14, fontweight='bold')
    plt.title("J-V Curves", fontsize=16, fontweight='bold')

    if xlim and len(xlim) == 2 and xlim[0] is not None and xlim[1] is not None:
        plt.xlim(xlim)
    if ylim and len(ylim) == 2 and ylim[0] is not None and ylim[1] is not None:
        plt.ylim(ylim)

    plt.legend(fontsize=10, frameon=False)
    plt.tight_layout()
    plt.show()