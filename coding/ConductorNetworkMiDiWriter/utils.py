# utils.py
import os.path

def makeModelFileMessage(modelPath):
        existsVis = True
        notVis = False
        if os.path.exists(modelPath):
            # figure out a way to elegantly make a new model
            modelMessage = 'Create a model.\nModel file exits at: ' + modelPath + ' Use this model?'
            existsVis = True #model exists
            notVis = False
        else:
            modelMessage = 'Create a model.\n\nNo model available at: ' + modelPath + ' Click okay to create a new one.\n'
            existsVis = False
            notVis = True
        return modelMessage, existsVis, notVis

def checkControlLog():
    controlPath = "data/test" + "/controls.csv"
    newControlData = [-1]
    if os.path.exists(controlPath):
        with open(controlPath, 'r') as csvfile:
            newControlData = list(csv.reader(csvfile, delimiter=","))
            print(f'newControlData: {newControlData}')
            
    return newControlData