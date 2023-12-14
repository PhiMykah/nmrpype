import nmrglue as ng
import matplotlib.pyplot as plt

dic, data = ng.pipe.read("hf/h.fid")

plt.plot(data)
plt.savefig("plot_1d.png")