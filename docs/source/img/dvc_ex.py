import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

plt.style.use("classic")
mpl.rcParams["figure.facecolor"] = "white"

if __name__ == "__main__":
    x_data = np.linspace(1, 500, 10, dtype=int)
    y_data_1 = np.array([0.01, 5, 17, 50, 78, 84, 90, 98, 99, 99])
    y_data_2 = np.array([0.04, 9, 21, 60, 85, 93, 97, 99, 99, 99])

    plt.plot(x_data, y_data_1, "o", label="Random")
    plt.plot(x_data, y_data_2, "x", label="Kaiming", zorder=5)
    plt.xlim(-5, 510)
    plt.ylim(-5, 110)
    plt.xlabel("No. Training Data Points")
    plt.ylabel("Accuracy %")
    plt.legend(loc=2)
    plt.grid()
    plt.savefig("NN_Accuracy.png", dpi=400, transparent=True)
    plt.show()
