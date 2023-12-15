import socketClient
import NeuralNetwork
import numpy as np

## Receives data from 2 sensors and does NN training and logging on the data in real time.
## WARNING this will start with fresh (random) weights and biases and OVERWRITE current model at pathPreface/model

basePath = "data/test/"

labelPath0 = "test"

pathList = [basePath + labelPath0]

#Input parameters
packetSize = 1
numSensors = 2
numClasses = 16

def main():


  #Testing data
  socketClient.createTrainingData(pathPreface=basePath, labelPath=labelPath0, packetLimit=20, label=0, packetSize=1, numSensors=2)

  #Train network with test data
  dataArr = np.load(basePath + "test.npy",allow_pickle=False)
  print(f'shape of data at basePath shape: {dataArr.shape}')
  print(f'data at basePath: {dataArr}')

  truthArr = np.load(basePath + "test_truth.npy",allow_pickle=False)
  print(f'shape of data at basePath shape: {truthArr.shape}')
  print(f'data at basePath: {truthArr}')

  NeuralNetwork.trainOrientation(basePath, pathList, packetSize, numSensors, numClasses)

if __name__ == "__main__": main()