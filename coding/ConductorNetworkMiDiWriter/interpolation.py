import numpy as np
from scipy.interpolate import interp1d
import cmake_example


# Uses pybind11 to transform the c++ function add into a python module.


number = cmake_example.add(8, 2)

print(number)

#Interpolation code from ChatGPT - Doesn't work

# # Generate random data for x, y, and z acceleration
# t = np.linspace(0, 10, num=1000)
# x = np.random.normal(0, 1, size=(len(t),))
# y = np.random.normal(0, 1, size=(len(t),))
# z = np.random.normal(0, 1, size=(len(t),))

# # Define time points for resampling
# t_resampled = np.linspace(0, 10, num=200)

# # Linear interpolation
# f_linear_x = interp1d(t, x, kind='linear')
# f_linear_y = interp1d(t, y, kind='linear')
# f_linear_z = interp1d(t, z, kind='linear')
# x_linear = f_linear_x(t_resampled)
# y_linear = f_linear_y(t_resampled)
# z_linear = f_linear_z(t_resampled)

# # Cubic spline interpolation
# f_spline_x = interp1d(t, x, kind='cubic')
# f_spline_y = interp1d(t, y, kind='cubic')
# f_spline_z = interp1d(t, z, kind='cubic')
# x_spline = f_spline_x(t_resampled)
# y_spline = f_spline_y(t_resampled)
# z_spline = f_spline_z(t_resampled)

# # Fourier interpolation
# f_fourier_x = interp1d(t, x, kind='cubic')
# f_fourier_y = interp1d(t, y, kind='cubic')
# f_fourier_z = interp1d(t, z, kind='cubic')
# x_fourier = f_fourier_x(t_resampled)
# y_fourier = f_fourier_y(t_resampled)
# z_fourier = f_fourier_z(t_resampled)

# # # Wavelet interpolation
# # from pywt import WaveletPacket
# # wp = WaveletPacket(data=np.array([x, y, z]), wavelet='db1', mode='symmetric')
# # wp_resampled = wp.reconstruct(update=True)
# # x_wavelet = wp_resampled[0,:]
# # y_wavelet = wp_resampled[1,:]
# # z_wavelet = wp_resampled[2,:]
# # Plot the results
# import matplotlib.pyplot as plt
# fig, axs = plt.subplots(3, 1, figsize=(8, 8))
# axs[0].plot(t, x, 'b.')
# axs[0].plot(t_resampled, x_linear, 'r-')
# axs[0].plot(t_resampled, x_spline, 'g-')
# axs[0].plot(t_resampled, x_fourier, 'm-')
# #axs[0].plot(t_resampled, x_wavelet, 'c-')
# axs[0].set_ylabel('X acceleration')

# axs[1].plot(t, y, 'b.')
# axs[1].plot(t_resampled, y_linear, 'r-')
# axs[1].plot(t_resampled, y_spline, 'g-')
# axs[1].plot(t_resampled, y_fourier, 'm-')
# #axs[1].plot(t_resampled, y_wavelet, 'c-')
# axs[1].set_ylabel('Y acceleration')

# axs[2].plot(t, z, 'b.')
# axs[2].plot(t_resampled, z_linear, 'r-')
# axs[2].plot(t_resampled, z_spline, 'g-')
# axs[2].plot(t_resampled, z_fourier, 'm-')
# #axs[2].plot(t_resampled, z_wavelet, 'c-')
# axs[2].set_ylabel('Z acceleration')

# plt.xlabel('Time (s)')
# plt.show()