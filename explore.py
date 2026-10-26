import nrrd
import matplotlib.pyplot as plt

M, header = nrrd.read("MRHead_1.nrrd")   # שנה לשם הקובץ שלך
print(M.shape, M.dtype)
print(header)

plt.imshow(M[:, :, M.shape[2] // 2], cmap="gray")
plt.show()