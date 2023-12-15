#Use this to test out code snippets

import numpy as np
import sys

def reShapePlay():
    x = np.random.rand(1,4,3)

    print(f'Random Array (x) 1 * 4 * 3: {x}')

    y = np.random.rand(1,4,3)

    print(f'Random Array (y) 1 * 4 * 3: {y}')

    z = np.append(x, y, axis=0)

    print(f'z.shape[0]: {z.shape[0]}')

    print(f'x appended to y (z) 2 * 4 * 3: {z}')

    a = np.reshape(z, (z.shape[0] * 4,3))

    print(f'z reshaped (a) 8 * 4: {a}')

    b = np.reshape(a, (round(a.shape[0]/4),4,3))

    print(f'a reshaped (b) 8 * 4: {b}')

def appendInside(label):
    x = np.random.rand(2,4,3)

    print(f'Random Array (x) 1 * 4 * 3: {x}')

    y = np.resize(x, (2,4,4))

    print(f'Resized Array (y) 1 * 4 * 4: {y}')
    print(f'y.shape): {y.shape}')
    for i in range(2):
        for j in range(4):
            y[i,j,3] = label

    print(f'Appended Array (y) 1 * 4 * 3: {y}')

def arraySizes():
    zeros = np.zeros([1,3])
    print(f'zeros: {zeros}')
    moreZeros = np.zeros([1,3])
    zeros = np.append(zeros, moreZeros, axis=0)
    print(f'zeros: {zeros}')

#reShapePlay()
#appendInside(1)
#print(sys.getrecursionlimit())

# x = np.zeros([1,2,6])
# print(f'x: {x}')
# y = x.copy()
# print(f'y: {y}')
# z = np.append(x,y,axis=0)
# #z.append(x)
# print(f'z: {z}')
# print(f'np.shape(z): {np.shape(z)}')
# z = np.append(z,y,axis=0)
# #z.append(x)
# print(f'z: {z}')
# print(f'np.shape(z): {np.shape(z)}')

# z[0:1:1,1:2:1,0:1:1] = 10
# print(f'z: {z}')
# print(f'np.shape(z): {np.shape(z)}')
arraySizes()


