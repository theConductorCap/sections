
# Generic Neural Network code from 
# H. Kinsley & D. Kukiela, Neural Networks from Scratch in Python, 2020.

import numpy as np
import itertools
import sys
import time
import nnfs
from nnfs.datasets import spiral_data
from nnfs.datasets import sine_data
import matplotlib.pyplot as plt
import math
import pickle
import copy
import os.path
import socketClient
import dill

nnfs.init()

#Use Model.set_parameters .get_parameters to set weights and biases of layers - takes uses a 1-D list
#Use model.save_parameters .load_parameters to save and load weigths and biases to a file
#When you load paramters from a file the model must be exactly the same as the model used to create the parameters

#Model.save and .load save and load the whole model



class Layer_Dense:
    #A class to define a fully connected layer
    #Layer initialization with random weights and biases of 0
    # n_inputs is number of inputs to layer
    # n_neurons is number of neurons in layer 
    def __init__(self, n_inputs, n_neurons, weight_regularizer_l1=0, weight_regularizer_l2=0, bias_regularizer_l1=0, bias_regularizer_l2=0):
        #inputs dot neurons
        self.weights = 0.01 * np.random.randn(n_inputs, n_neurons) 
        self.biases = np.zeros((1, n_neurons))
        self.weight_regularizer_l1 = weight_regularizer_l1
        self.weight_regularizer_l2 = weight_regularizer_l2
        self.bias_regularizer_l1 = bias_regularizer_l1
        self.bias_regularizer_l2 = bias_regularizer_l2
        
    #Forward Pass
    def forward(self, inputs, training):
        self.inputs = inputs
        self.output = np.dot(inputs, self.weights) + self.biases
        
    #Backward Pass
    def backward(self, dvalues):
        #Gradients on parameters
        self.dweights = np.dot(self.inputs.T, dvalues)
        self.dbiases = np.sum(dvalues, axis=0, keepdims=True)
        
        #Gradients on regularization
        #L1 on weights
        if self.weight_regularizer_l1 > 0:
            dL1 = np.ones_like(self.weights)
            dL1[self.weights < 0] = -1
            self.dweights += self.weight_regularizer_l1 * dL1 
        
        #L2 on weights
        if self.weight_regularizer_l2 > 0:
            self.dweights += 2 * self.weight_regularizer_l2 * self.weights
            
        #L1 on biases
        if self.bias_regularizer_l1 > 0:
            dL1 = np.ones_like(self.biases)
            dL1[self.biases < 0] = -1
            self.dbiases += self.bias_regularizer_l1 * dL1 
        
        #L2 on weights
        if self.bias_regularizer_l2 > 0:
            self.dbiases += 2 * self.bias_regularizer_l2 * self.biases    
        
        #Gradient on values
        self.dinputs = np.dot(dvalues, self.weights.T)
        
    #retreive layer parameters
    def get_parameters(self):
        return self.weights, self.biases
    
    def set_parameters(self, weights, biases):
        self.weights = weights
        self.biases = biases
        
#Dropout
class Layer_Dropout:
    #Init
    def __init__(self,rate):
        #Store rate, inverted
        self.rate = 1 - rate
        
    #Forward Pass
    def forward(self, inputs, training):
        #Save input values
        self.inputs = inputs
        
        #If not training no need for drop out use the whole layer
        if not training:
            self.output = inputs.copy()
            return
        
        #Generate and save scaled mask
        self.binary_mask = np.random.binomial(1, self.rate, size=inputs.shape) / self.rate

        #Apply mask to output values
        self.output = inputs * self.binary_mask
        
    #Backward pass
    def backward(self, dvalues):
        #Gradient on values
        self.dinputs = dvalues * self.binary_mask

#Input layer
class Layer_Input:
    #forward pass
    def forward(self, inputs, training):
        self.output = inputs
    
    
class Activation_ReLu:
    #returns 0 if input less than 0 or input
    #Works best for hidden layers
    
    #Forward pass
    def forward(self, inputs, training):
        #calculate output values form input
        self.inputs = inputs
        self.output = np.maximum(0, inputs)
        
    def backward(self, dvalues):
        #Since we need to modify the original variable make a copy
        self.dinputs = dvalues.copy()
        
        #Zero gradient where input values were negative
        self.dinputs[self.inputs <= 0] = 0
        
    #Calculate predictions for outputs
    def predictions(self, outputs):
        return outputs
        
        
class Activation_Softmax:
    #Exponantes inputs and devides by sum of input exponents
    #Good for output layer activation when classifying
    
    def forward(self, inputs, training):
        
        self.inputs = inputs
        
        #Get unnormalized probabilities (subtract highest value to avoid explosion - gives 0 or a negative)
        exp_values = np.exp(inputs - np.max(inputs, axis=1, keepdims=True))
        
        #Normalize for each sample
        probabilities = exp_values / np.sum(exp_values, axis=1, keepdims=True)
        
        self.output = probabilities
        
    #Backward Pass
    def backward(self, dvalues):
        #create unitialized array
        self.dinputs = np.empty_like(dvalues)
        
        #Enumerate outputs and gradients
        for index, (single_output, single_dvalues) in enumerate(zip(self.output, dvalues)):
            
            #flatten output array
            single_output = single_output.resahpe(-1,1)
            #calculate Jacopbin matric of the output
            jacobin_matrix = np.daigflat(single_output) - np.dot(single_output, single_output.T)
            #calculate sample-wise gradient and add to array of sample gradients
            self.dinputs[index] = np.dot(jacobin_matrix, single_dvalues)
            
    #Calculate predictions for outputs
    def predictions(self, outputs):
        return np.argmax(outputs, axis=1)
            
#Sigmoid optimization - for binary regression
class Activation_Sigmoid:
    
    #Forward Pass
    def forward(self, inputs, training):
        #save input and calculate/save output
        self.inputs = inputs
        self.output = 1 / (1 + np.exp(-inputs))
        
    #Backward Pass
    def backward(self, dvalues):
        #derivative - caculates from output of sigmoid
        self.dinputs = dvalues * (1- self.output) * self.output
        
    #Calculate predictions for outputs
    def predictions(self, outputs):
        return (outputs > 0.5) * 1
 
#Linear Activation - for regression
class Activation_Linear:
    
    #Forward pass
    def forward(self, inputs, training):
        #Just remember the values
        self.inputs = inputs
        self.output = inputs
        
    #Backward pass
    def backward(self, dvalues):
        #derivative is 1, 1 * dvalues = dvalues
        self.dinputs = dvalues.copy()
        
    #Calculate predictions for outputs
    def predictions(self, outputs):
        return outputs
    
#Stocastic Gradient Descent - with learning rate decay and momentum        
class Optimizer_SGD:
    
    #Initialize optimzer - set settings,
    #learning rate of 1. is defualt for this optimizer
    
    def __init__(self, learning_rate=1.0, decay=0, momentum=0):
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.momentum = momentum
    
    #Call once before any parameter updates    
    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1./(1. + self.decay * self.iterations))
        
    #update parameters
    def update_params(self, layer):
        
        #if we use momentum
        if self.momentum:
            #If layer does not contain momentum arrays, create them
            if not hasattr(layer, 'weight_momentums'):
                layer.weight_momentums = np.zeros_like(layer.weights)
                layer.bias_momentums = np.zeros_like(layer.biases)
                
            #Build weight updates with momentum - use previous updates multiplied by retain facter and update current gradients
            weight_updates = self.momentum * layer.weight_momentums - self.current_learning_rate * layer.dweights
            layer.weight_momentums = weight_updates
            
            #Build bias updates
            bias_updates = self.momentum * layer.bias_momentums - self.current_learning_rate * layer.dbiases
            layer.bias_momentums = bias_updates
            
        #Vanilla SGD updates (no momentum)
        else:
            weight_updates = -self.current_learning_rate * layer.dweights
            bias_updates = -self.current_learning_rate * layer.dbiases   
            
        #Update weights and biases  
        layer.weights += weight_updates
        layer.biases += bias_updates
    
    #Call once after any parameter updates    
    def post_update_params(self):
        self.iterations += 1

#Adagrad optimizer - scales correction of weights and biases to previous corrections - less corrected values get bigger moves
class Optimizer_AdaGrad:
    
    #Initialize optimzer - set settings,
    #learning rate of 1. is defualt for this optimizer
    
    def __init__(self, learning_rate=1.0, decay=0, epsilon=1e-7):
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.epsilon= epsilon
    
    #Call once before any parameter updates    
    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1./(1. + self.decay * self.iterations))
        
    #update parameters
    def update_params(self, layer):

        #If layer does not contain cache arrays, create them
        if not hasattr(layer, 'weight_cache'):
            layer.weight_cache = np.zeros_like(layer.weights)
            layer.bias_cache = np.zeros_like(layer.biases)
            
        #Update cache with squared current gradients
        layer.weight_cache += layer.dweights**2
        layer.bias_cache += layer.dbiases**2
        
        #Vanilla SGD parameter update and normalization  
        layer.weights += -self.current_learning_rate * layer.dweights / (np.sqrt(layer.weight_cache) + self.epsilon)
        layer.biases += -self.current_learning_rate * layer.dbiases / (np.sqrt(layer.bias_cache) + self.epsilon)
    
    #Call once after any parameter updates    
    def post_update_params(self):
        self.iterations += 1

#Root Mean Square Propagation - cache is a moving average determined by rho (cache memory decay rate)
#Method carries momentum of gradients and learning rate so start with a small learning rate (~0.001)
class Optimizer_RMSProp:
    
    #Initialize optimzer - set settings,
    #learning rate of 1. is defualt for this optimizer
    
    def __init__(self, learning_rate=0.001, decay=0, epsilon=1e-7, rho=0.9):
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.epsilon= epsilon
        self.rho = rho
    
    #Call once before any parameter updates    
    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1./(1. + self.decay * self.iterations))
        
    #update parameters
    def update_params(self, layer):

        #If layer does not contain cache arrays, create them
        if not hasattr(layer, 'weight_cache'):
            layer.weight_cache = np.zeros_like(layer.weights)
            layer.bias_cache = np.zeros_like(layer.biases)
            
        #Update cache with squared current gradients
        layer.weight_cache = self.rho * layer.weight_cache + (1 - self.rho) * layer.dweights**2
        layer.bias_cache = self.rho * layer.bias_cache + (1 - self.rho) * layer.dbiases**2
        
        #Vanilla SGD parameter update and normalization  
        layer.weights += -self.current_learning_rate * layer.dweights / (np.sqrt(layer.weight_cache) + self.epsilon)
        layer.biases += -self.current_learning_rate * layer.dbiases/ (np.sqrt(layer.bias_cache) + self.epsilon)
    
    #Call once after any parameter updates    
    def post_update_params(self):
        self.iterations += 1

#Adaptive Momentum: SGD with momentum + RMSProp
#Applies momentum and then per weight adaptive learning
#Uses beta1 and beta2 to divide by a fraction in early steps and then increase to fractions value to reduce impact in pater steps
class Optimizer_Adam:
    
    #Initialize optimzer - set settings,
    #learning rate of 1. is defualt for this optimizer
    
    def __init__(self, learning_rate=0.001, decay=0, epsilon=1e-7, beta_1 = 0.9, beta_2 = 0.999):
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.epsilon= epsilon
        self.beta_1 = beta_1
        self.beta_2 = beta_2
    
    #Call once before any parameter updates    
    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1/(1 + self.decay * self.iterations))
   
    #update parameters
    def update_params(self, layer):

        #If layer does not contain cache arrays, create them
        if not hasattr(layer, 'weight_cache'):
            layer.weight_momentums = np.zeros_like(layer.weights)
            layer.weight_cache = np.zeros_like(layer.weights)
            layer.bias_momentums = np.zeros_like(layer.biases)
            layer.bias_cache = np.zeros_like(layer.biases)
        
        #Update momentum with current gradients
        layer.weight_momentums = self.beta_1 * layer.weight_momentums + (1 - self.beta_1) * layer.dweights
        layer.bias_momentums = self.beta_1 * layer.bias_momentums + (1 - self.beta_1) * layer.dbiases
        
        #Get Corrected momentum - self.iteration is 0 at first pass and we need to start at 1
        weight_momentums_corrected = layer.weight_momentums / (1 - self.beta_1 ** (self.iterations + 1))
        bias_momentums_corrected = layer.bias_momentums / (1 - self.beta_1 ** (self.iterations + 1))
        
        #Update cache with squared current gradients
        layer.weight_cache = self.beta_2 * layer.weight_cache + (1 - self.beta_2) * layer.dweights**2
        layer.bias_cache = self.beta_2 * layer.bias_cache + (1 - self.beta_2) * layer.dbiases**2
        
        #Get corrected cache
        weight_cache_corrected = layer.weight_cache / (1 - self.beta_2 ** (self.iterations + 1))
        bias_cache_corrected = layer.bias_cache / (1 - self.beta_2 ** (self.iterations + 1))
        
        #print(f'layer.weights before : {layer.weights}')
        
        #Vanilla SGD parameter update and normalization  
        layer.weights += -self.current_learning_rate * weight_momentums_corrected / (np.sqrt(weight_cache_corrected) + self.epsilon)
        #print(f'weights: {layer.weights}')
        layer.biases += -self.current_learning_rate * bias_momentums_corrected / (np.sqrt(bias_cache_corrected) + self.epsilon)
        #print(f'biases: {layer.biases}')
        
        #print(f'layer.weights after : {layer.weights}')
    
    #Call once after any parameter updates    
    def post_update_params(self):
        self.iterations += 1
 
#Common Loss Class        
class Loss:
    
    #Regularization loss calculation
    def regularization_loss(self,layer):
        #0 by default
        regularization_loss = 0
        
        #L1 regularization weights
        #only calculate when factor is greater than 0
        if layer.weight_regularizer_l1 > 0:
            regularization_loss += layer.weight_regularizer_l1 * np.sum(np.abs(layer.weights))
        
        #L2 regularization weights
        if layer.weight_regularizer_l2 > 0:
            regularization_loss += layer.weight_regularizer_l2 * np.sum(layer.weights * layer.weights)

        #L1 regularization biases
        if layer.bias_regularizer_l1 > 0:
            regularization_loss += layer.bias_regularizer_l1 * np.sum(np.abs(layer.biases))
        
        #L2 regularization biases
        if layer.bias_regularizer_l2 > 0:
            regularization_loss += layer.bias_regularizer_l2 * np.sum(layer.biases * layer.biases)
        
        return regularization_loss
    
    #set / remember trainable layers
    def remember_trainable_layers(self, trainable_layers):
        self.trainable_layers = trainable_layers
        
    #Calculates the data and regularization losses
    #given model output and ground truth values
    def calculate(self, output, y, *, include_regularization=False):
        
        #Calculate sample losses
        sample_losses = self.forward(output, y)
        
        #Calculate mean loss
        data_loss = np.mean(sample_losses)
        
        #Add accumulated sum of losses and sample count
        self.accumulated_sum += np.sum(sample_losses)
        self.accumulated_count += len(sample_losses)
        
        #if just data loss then return it
        if not include_regularization:
            return data_loss
        
        #Return the data and regularization losses
        return data_loss, self.regularization_loss()
        
        #print(f'data_loss: {data_loss}')
    
    def regularization_loss(self):
        # 0 by default
        regularization_loss = 0
        
        #Calculate regulaization loss for all trainable layers
        for layer in self.trainable_layers:
            #L1 regularization - weights
            if layer.weight_regularizer_l1 > 0:
                regularization_loss += layer.weight_regularizer_l1 * np.sum(np.abs(layer.weights))
            
            #l2 regularization - weights
            if layer.weight_regularizer_l2 > 0:
                regularization_loss += layer.weight_regularizer_l2 * np.sum(np.abs(layer.weights * layer.weights))
                
            #L1 regularization - bias
            if layer.bias_regularizer_l1 > 0:
                regularization_loss += layer.bias_regularizer_l1 * np.sum(np.abs(layer.biases))
            
            #l2 regularization - bias
            if layer.bias_regularizer_l2 > 0:
                regularization_loss += layer.bias_regularizer_l2 * np.sum(np.abs(layer.biases * layer.biases))
        
        return regularization_loss
    
    #Calculate accumulated loss
    def calculate_accumulated(self, *, include_regularization=False):
        
        #Calculate mean loss
        data_loss = self.accumulated_sum / self.accumulated_count
        
        #If just data loss return it
        if not include_regularization:
            return data_loss
        
        return data_loss, self.regularization_loss()
    
    def new_pass(self):
        self.accumulated_sum = 0
        self.accumulated_count = 0

class Loss_CategoricalCrossEntropy(Loss):   
    #Forward pass
    def forward(self, y_pred, y_true):
        
        #Number of sample in a batch
        samples = len(y_pred)
        
        # print(f'len(y_pred): {len(y_pred)}') 
        # print(f'len(y_pred): {len(y_pred)}') 
        # print(f'y_true: {y_true}') 
        
        #Clip data to prevent division by 0
        #Clip both sidfes to not drag mean towards any value
        y_pred_clipped = np.clip(y_pred, 1e-7, 1 - 1e-7)
        
        #print(f'y_pred_clipped: {y_pred_clipped}') 
        
        #Probabilities for target values
        #Only if categorical labels
        if len(y_true.shape) == 1:
            # print(f'samples): {samples}') 
            # print(f'y_pred_clipped: {y_pred_clipped}')
            # print(f'len(y_pred_clipped): {len(y_pred_clipped)}')
            correct_confidences = y_pred_clipped[range(samples), y_true]
        
        #Mask values - only for one-hot encoded labels
        elif len(y_true.shape) == 2:
            correct_confidences = np.sum(y_pred_clipped * y_true, axis=1)
        
        #print(f'correct_confidences: {correct_confidences}')    
            
        #Losses
        negative_log_likelihoods = -np.log(correct_confidences)
        
        #print(f'cnegative_log_likelihoods: {negative_log_likelihoods}')
        
        return negative_log_likelihoods
    
    #backward pass
    def backward(self, dvalues, y_true):
        #number of samples
        samples = len(dvalues)
        
        #number of labels in every sample
        labels = len(dvalues[0])
        
        #if lables are sparse, turn them into one-hot vector
        if len(y_true.shape) == 1:
            y_true = np.eye(labels)[y_true]
        
        #calculate gradient
        self.dinputs = y_true / dvalues
        
        #normalize gradient
        self.dinputs = self.dinputs / samples
    
#Softmax classifier - combines softmax activation and cross-entropy loss to speed up backward step
class Activation_Softmax_Loss_CategoricalCrossEntropy():
    
    #backward pass
    def backward(self, dvalues, y_true):
        
        #Number of samples
        samples = len(dvalues)
        
        #If labels are one-hot encoded turn them into discrete values
        if len(y_true.shape) == 2:
            y_true = np.argmax(y_true, axis=1)
            
        #copy so we can safely modify
        self.dinputs = dvalues.copy()
        
        #calculate gradient
        self.dinputs[range(samples), y_true] -= 1
        
        #normalize gradient
        self.dinputs = self.dinputs / samples
        
class Loss_BinaryCrossentropy(Loss):
    
    #Forward Pass
    def forward(self, y_pred, y_true):
        #Clip data to prevent division by 0
        y_pred_clipped = np.clip(y_pred, 1e-7, 1-1e-7)
        
        #Calculate sample-wise loss
        sample_losses = -(y_true * np.log(y_pred_clipped) + (1 - y_true) * np.log(1 - y_pred_clipped))
        
        sample_losses = np.mean(sample_losses, axis=-1)
        
        return sample_losses
    
    def backward(self, dvalues, y_true):
        
        #Number of samples
        samples = len(dvalues)
        
        #Number of outputs in every sample
        outputs = len(dvalues[0])
        
        #clip data to prevent division by 0
        clipped_dvalues = np.clip(dvalues, 1e-7, 1- 1e-7)
        
        #calculate gradient
        self.dinputs = -(y_true / clipped_dvalues - (1-y_true) / (1 - clipped_dvalues)) / outputs
        
        #Normailize gradient
        self.dinputs = self.dinputs / samples
    
 #Mean Squared Error Loss - used for regression
class Loss_MeanSquaredError(Loss): #L2 Loss
     
    #Forward Pass
    def forward(self, y_pred, y_true):
        #Calculate loss
        sample_losses = np.mean((y_true - y_pred)**2, axis=-1)
        
        return sample_losses
    
    #Backward pass
    def backward(self, dvalues, y_true):
        #number of samples
        samples = len(dvalues)
        
        #number of outputs
        outputs = len(dvalues[0])
        
        #Gradient on values
        self.dinputs = -2 * (y_true - dvalues) / outputs
        #Normalize gradient
        self.dinputs = self.dinputs / samples

#Mean Absolute Error Loss - used for regression (but not as good as squared version)
class Loss_MeanAbsoluteError(Loss): #L1 Loss
    def forward(self, y_pred, y_true):
        
        #Calculate loss
        sample_losses = np.mean(np.abs(y_true -y_pred), axis=-1)
        
        return sample_losses
    
    def backward(self, dvalues, y_true):
        
        samples = len(dvalues) 
        outputs = len(dvalues[0])
        
        #gradient
        self.dinputs = np.sign(y_true - dvalues) / outputs
        self.dinputs = self.dinputs / samples

#Common accuracy class
class Accuracy:
    #Calculates and accuracy
    def calculate(self, predictions, y):
        
        #Get comparison results
        comparisons = self.compare(predictions, y)
        
        #Calculate an accuracy
        accuracy = np.mean(comparisons)
        
        #Add accumulated sum of matching values and sample count
        self.accumulated_sum += np.sum(comparisons)
        self.accumulated_count += len(comparisons)
        
        return accuracy
    
    def calculate_accumulated(self):
        
        #calculate an accuracy
        accuracy = self.accumulated_sum / self.accumulated_count

        return accuracy
    
    def new_pass(self):
        self.accumulated_sum = 0
        self.accumulated_count = 0
        
#Accuracy calculation for regression model    
class Accuracy_Regression(Accuracy):
    def __init__(self):
        #create precision property
        self.precision = None
        
    #Calculates precision value based on ground truth
    def init(self, y, reinit=False):
        if self.precision is None or reinit:
            self.precision = np.std(y) / 250
    
    #Compares predictions to the ground truth values
    def compare(self, predictions, y):
        return np.absolute(predictions -y) < self.precision    
    

class Accuracy_Categorical(Accuracy):
    #No init needed
    def init(self, y):
        pass
    
    #Compares predictions to the ground truth values
    def compare(self, predictions, y):
        if len(y.shape) == 2:
            y = np.argmax(y, axis=1)
        return predictions == y        


#Model Class
class Model:
    def __init__(self):
        #create a list of network objects
        self.layers = []
        self.softmax_classifier_output = None
        
    #add objects to the model
    def add(self, layer):
        self.layers.append(layer)

    #Set loss and optimizer
    def set(self, *, loss, optimizer, accuracy):
        if loss is not None:
            self.loss = loss
        if optimizer is not None:
            self.optimizer = optimizer
        if accuracy is not None:
            self.accuracy = accuracy
     
    #Finalize the model
    def finalize(self):
        #create and set the input layer
        self.input_layer = Layer_Input()
        
        #Count all the objects
        layer_count = len(self.layers)
        
        #initilize a list containing trainable layers
        self.trainable_layers = []
        
        #Iterate the objects
        for i in range(layer_count):
            
            #If its the first layer the previous layer object is the input layer
            if i == 0:
                self.layers[i].prev = self.input_layer
                self.layers[i].next = self.layers[i+1]
                
            #All layers except first and last
            elif i < layer_count - 1:
                self.layers[i].prev = self.layers[i-1]
                self.layers[i].next = self.layers[i+1]
                
            #The last layer - the next object is the loss
            #Also the models output, we will save it 
            else:
                self.layers[i].prev = self.layers[i-1]
                self.layers[i].next = self.loss
                self.output_layer_activation = self.layers[i]   
            
            #If layer has weights it is trainable    
            if hasattr(self.layers[i], 'weights'):
                self.trainable_layers.append(self.layers[i])
                
        #Update loss object with trainable layers
        if self.loss is not None:
            self.loss.remember_trainable_layers(self.trainable_layers)
        
        #If output activation is softmax and loss function is categorical cross entropy - can speed up the process
        if isinstance(self.layers[-1], Activation_Softmax) and isinstance(self.loss, Loss_CategoricalCrossEntropy):
            #Create an object of combined activation and loss functions
            self.softmax_classifier_output = Activation_Softmax_Loss_CategoricalCrossEntropy()
                
    #Train the model
    def train(self, X, y, *, epochs=1, batch_size = None,print_every=1, validation_data=None):
        
        #initilizae accuracy object
        self.accuracy.init(y)
        
        #Default value if batch size is not being set
        train_steps = 1
        
        #If there is validation data passed set default number of steps
        if validation_data is not None:
            validation_steps = 1
            
            #for better readability
            X_val, y_val = validation_data
            
        #Calculate number of steps
        if batch_size is not None:
            train_steps = len(X) // batch_size
            
            #Division rounds down, so add another step if there is a remainder
            if train_steps * batch_size < len(X):
                train_steps += 1
                
            if validation_data is not None:
                validation_steps = len(X_val) // batch_size  

                if validation_steps * batch_size < len(X_val):
                    validation_steps += 1
        
        #Main training loop
        for epoch in range(1, epochs+1):
            
            print(f'Epoch: {epoch}')
            
            #Reset accumulated values in loss and accuracy
            self.loss.new_pass()
            self.accuracy.new_pass()
            
            #iterate over steps
            for step in range(train_steps):
                if batch_size is None:
                    batch_X = X
                    batch_y = y
                
                else:
                    batch_X = X[step * batch_size:(step+1) * batch_size]
                    batch_y = y[step * batch_size:(step+1) * batch_size]
            
                #Perform the forward pass
                output = self.forward(batch_X, training=True)
                
                #Calculate loss
                data_loss, regularization_loss = self.loss.calculate(output, batch_y, include_regularization=True)
                loss = data_loss + regularization_loss
                
                #get predictions and calculate an accuracy
                predictions = self.output_layer_activation.predictions(output)
                accuracy = self.accuracy.calculate(predictions, batch_y)
                
                #backward pass
                self.backward(output, batch_y)
                
                #Optimize
                self.optimizer.pre_update_params()
                for layer in self.trainable_layers:
                    self.optimizer.update_params(layer)
                self.optimizer.post_update_params()
                
                # if not step % print_every or step == train_steps - 1:
                #     print(f'Step: {step}, ' + 
                #         f'acc: {accuracy:.3f}, ' + 
                #         f'loss: {loss:.3f}, ' + 
                #         f'data_loss: {data_loss:.3f}, ' + f'regularization loss: {regularization_loss:.3f}, ' + 
                #         f'lr: {self.optimizer.current_learning_rate}')
        
            #Get and print epoch loss and accuracy
            epoch_data_loss, epoch_regularization_loss = self.loss.calculate_accumulated(include_regularization=True)
            epoch_loss = epoch_data_loss + epoch_regularization_loss
            epoch_accuracy = self.accuracy.calculate_accumulated()
            
            print(f'training, ' + 
                        f'acc: {epoch_accuracy:.3f}, ' + 
                        f'loss: {epoch_loss:.3f}, ' + 
                        f'data_loss: {epoch_data_loss:.3f}, ' + f'regularization loss: {epoch_regularization_loss:.3f}, ' + 
                        f'lr: {self.optimizer.current_learning_rate}')
                
            #If there is validation data
            if validation_data is not None:
                #evaluate the model
                self.evaluate(*validation_data, batch_size=batch_size)
                  
    def forward(self, X, training):
        #Call forward method on the input layer
        self.input_layer.forward(X, training)
        
        #Call forward method on every object in a chain
        for layer in self.layers:
            layer.forward(layer.prev.output, training)
        
        #layer is now the last object in the list
        return layer.output
        
    #Backwards!
    def backward(self, output, y):
               
        #Softmax classifier speed boost
        if self.softmax_classifier_output is not None:
            #first call backward method on combined activation / loss to set dinputs properly
            self.softmax_classifier_output.backward(output,y)

            #Can do two layers at once
            self.layers[-1].dinputs = self.softmax_classifier_output.dinputs
            
            #call backward method going through
            for layer in reversed(self.layers[:-1]):
                layer.backward(layer.next.dinputs)     
   
            return
   
        #Fist call backward method on the loss to set dinputs propety used in back propagation
        self.loss.backward(output, y)

        #Call backward method going through all the objects in reverse order passing dinputs through
        for layer in reversed(self.layers):
            layer.backward(layer.next.dinputs)  
    
    #Evaluate the model with passed in dataset        
    def evaluate(self, X_val, y_val, *, batch_size=None):
        #default batch size if batch_size not set
        validation_steps = 1
        
        #Calculate number of steps
        if batch_size is not None:
            validation_steps = len(X_val) // batch_size
            
            if validation_steps * batch_size < len(X_val):
                validation_steps += 1
                
        #Reset accumulated loss and accuracy
        self.loss.new_pass()
        self.accuracy.new_pass()
        
        for step in range(validation_steps):
            #if batch is not set use full testing data set
            if batch_size is None:
                batch_X = X_val
                batch_y = y_val
            
            else:
                batch_X = X_val[step * batch_size:(step+1) * batch_size]
                batch_y = y_val[step * batch_size:(step+1) * batch_size]
            
            #perform the forward pass
            output = self.forward(batch_X, training=False)
            
            #Calculate loss
            loss = self.loss.calculate(output, batch_y)
            
            #Get predictions and calculate accuracy
            predictions = self.output_layer_activation.predictions(output)
            accuracy = self.accuracy.calculate(predictions, batch_y)
            
        validation_loss = self.loss.calculate_accumulated()
        validation_accuracy = self.accuracy.calculate_accumulated()
        
        #Print summary
        print(f'validation, ' + 
                f'acc: {accuracy:.3f}, ' + 
                f'loss: {loss:.3f}')
        
    #Retrieves and returns parameters of trainable layers
    def get_parameters(self):
        
        #create a list for parameters
        parameters = []
        
        #iterable trainable layers and get their parameters
        for layer in self.trainable_layers:
            parameters.append(layer.get_parameters())
            
        return parameters
    
    def set_parameters(self, parameters):
        for parameter_set, layer in zip(parameters, self.trainable_layers):
            layer.set_parameters(*parameter_set)
            
    #Saves parameters to a file
    def save_parameters(self, path):
        #Open a file in binary write mode
        with open(path, 'wb') as f:
            pickle.dump(self.get_parameters(), f)
            
    def load_parameters(self, path):
        #Open file in binary read mode
        with open(path, 'rb') as f:
            self.set_parameters(pickle.load(f))
            
    #Save the model
    def save(self, path):
        model = copy.deepcopy(self)
        
        #reset accumulated values in loss and accuracy objects
        model.loss.new_pass()
        model.accuracy.new_pass()

        #remove data in input layer and reset gradients
        model.input_layer.__dict__.pop('output', None)
        model.loss.__dict__.pop('dinputs', None)
        
        #For each layer remove inputs, outputs and dinputs
        for layer in model.layers:
            for property in ['inputs', 'output', 'dinputs', 'dweights', 'dbiases']:
                layer.__dict__.pop(property, None)
                
        #Open a file and dump the model data
        with open(path, 'wb') as f:
            dill.dump(model, f)
            
    #loads and returns a model
    @staticmethod
    def load(path):
        with open(path, 'rb') as f:
            model = dill.load(f)
            
        return model
    
    # Predicts on the samples
    def predict(self, X, *, batch_size=None):
        
        #Default value if batch size is not being used
        prediction_steps = 1
        
        #calculate number of steps
        if batch_size is not None:
            prediction_steps = len(X) //batch_size
            
            if prediction_steps * batch_size < len(X):
                prediction_steps += 1
                
        #Model outputs
        output = []
        
        #Iterate over steps
        for step in range(prediction_steps):
            #If batch size is not set train using one step
            if batch_size is None:
                batch_X = X
                
            else: 
                batch_X = X[step*batch_size:(step+1)*batch_size]

            #Forward pass
            batch_output = self.forward(batch_X, training=False)
            
            #Append batch prediction to the list of predictions
            output.append(batch_output)
            
            return np.vstack(output)


def getAccDataBinary(dataPathList, truthPathList, packetSize, numSensors):
    print()
    # print("**######################################**")    print("getAccDataBinary")
    dataArr = np.empty([1, 3 * packetSize * numSensors])
    dataArr[0,0] = 99.
    truthArr = np.empty([1,])
    truthArr[0] = 99

    for path in dataPathList:
        # print("****")
        print(f'data path: {path}')
        if os.path.exists(path):
            print("****")
            print(path)
            tmpArr = np.load(path,allow_pickle=False)

            if dataArr[0,0] == 99.:
                dataArr = tmpArr
                print(f'dataArr shape: {dataArr.shape}')
                print(f'dataArr from file: {dataArr}')
            else:
                #print(f'tmpArr shape: {tmpArr.shape}')
                #print(f'tmpArr from file: {tmpArr}')
                dataArr = np.append(dataArr, tmpArr,axis=0)
                print(f'dataArr shape: {dataArr.shape}')
                print(f'dataArr from file: {dataArr}')

    for path in truthPathList:
        print(f'Truth Patch in NN: {path}')
        if os.path.exists(path):
            print("****")
            print(path)
            tmpArr = np.load(path,allow_pickle=False)
            
            if truthArr[0] == 99:
                truthArr = tmpArr
            else:
                print(f'tmpArr shape: {tmpArr.shape}')
                print(f'tmpArr: {tmpArr}')
                truthArr = np.append(truthArr, tmpArr,axis=0)

    #Get random index
    dataIndex = np.arange(0 , dataArr.shape[0])
    np.random.shuffle(dataIndex)

    #print(f'dataArr shape: {dataArr.shape}')
    #print(f'dataArr from file: {dataArr}')
    #print(f'truthArr shape: {truthArr.shape}')
    #print(f'truthArr from file: {truthArr}')
    # print(f'dataIndex shape: {dataIndex.shape}')
    # print(f'dataIndex: {dataIndex}')

    dataTmp = dataArr.copy()
    truthTmp = truthArr.copy()
    for i in range(dataArr.shape[0]):
        dataArr[dataIndex[i]] = dataTmp[i]
        truthArr[dataIndex[i]] = truthTmp[i]

    print(f'dataArr shape: {dataArr.shape}')
    print(f'dataArr from file: {dataArr}')
    print(f'truthArr shape: {truthArr.shape}')
    print(f'truthArr randomized: {truthArr}')
    print(f'dataIndex shape: {dataIndex.shape}')
    print(f'dataIndex from file: {dataIndex}')

    return dataArr, truthArr

def getAccDataCSV(dataPathList, truthPathList):
    # print()
    # print("**######################################**")
    # print("Text Data")
    dataArr = np.empty([1,30])
    dataArr[0,0] = 99.
    truthArr = np.empty([1,1])
    truthArr[0,0] = 99.
    print(f'truthArr init: {truthArr}')
    print(f'dataArr init: {truthArr}')
    for path in dataPathList:
        if os.path.exists(path):
            # print("****")
            # print(path)
            tmpArr = np.loadtxt(path,dtype=float, delimiter=',', ndmin = 2)

            if dataArr[0,0] == 99.:
                dataArr = tmpArr
            else:
                #print(f'tmpArr shape: {tmpArr.shape}')
                #print(f'tmpArr from file: {tmpArr}')
                dataArr = np.append(dataArr, tmpArr,axis=0)
            
        
    for path in truthPathList:
        if os.path.exists(path):
            # print("****")
            # print(path)
            tmpArr = np.loadtxt(path,dtype=int, delimiter=',', ndmin = 2)
            
            if truthArr[0,0] == 99.:
                truthArr = tmpArr
            else:
                # print(f'tmpArr shape: {tmpArr.shape}')
                # print(f'tmpArr: {tmpArr}')
                truthArr = np.append(truthArr, tmpArr,axis=0)

    #Get random index
    dataIndex = np.arange(0 , dataArr.shape[0])
    np.random.shuffle(dataIndex)

    #print(f'dataArr shape: {dataArr.shape}')
    #print(f'dataArr from file: {dataArr}')
    #print(f'truthArr shape: {truthArr.shape}')
    #print(f'truthArr from file: {truthArr}')
    # print(f'dataIndex: {dataIndex.shape}')
    # print(f'truthArr from file: {dataIndex}')

    dataTmp = dataArr.copy()
    truthTmp = truthArr.copy()
    for i in range(dataArr.shape[0]):
        dataArr[dataIndex[i]] = dataTmp[i]
        truthArr[dataIndex[i]] = truthTmp[i]

    #print(f'dataArr shape: {dataArr.shape}')
    #print(f'dataArr from file: {dataArr}')
    #print(f'truthArr shape: {truthArr.shape}')
    #print(f'truthArr from file: {truthArr}')

    return dataArr, truthArr       


def convertTruthCSV(truthPathList):
    #One time function to convert truth data to a 1-D array - done automatically in socketClient from now on
    for path in truthPathList:
        if os.path.exists(path):
            # print("****")
            # print(path)
            y = np.loadtxt(path,dtype=int, delimiter=',') 
            print(y)
            print(y.shape)
            y = y.reshape(y.shape[0])  #reshape truth data only if truth data is formatted as 2-D
            print(y)
            print(y.shape)
            np.savetxt(path, y, fmt="%d", delimiter=",")
    for path in truthPathList:   #Check that the file was written to properly
         if os.path.exists(path):
            y = np.loadtxt(path,dtype=int, delimiter=',') 
            print(y)
            print(y.shape)

def convertPickletoDill():
    model = Model.load('data/AccModel01')
    print(f'model: {model}')

    #Open a file and dump the model data
    with open("data/AccModel01Dill", 'wb') as f:
        dill.dump(model, f)

def realTimePrediction(packetData, pathPreface):
     #Create Dataset
    predictionStartMs = int(time.time() * 1000)
    predictions = []
    model = Model.load(pathPreface + "/model.model")
    #print(f'model: {model}')
    
    confidences = model.predict(packetData)
    
    confidencesPath = pathPreface + "/confidences.npy"
    #Write Confidences to binary
    if os.path.exists(confidencesPath):
        tmpArr = np.load(confidencesPath,allow_pickle=False)
        #print(f'confidences from file: {tmpArr}')
        tmpArr = np.append(tmpArr,confidences, axis=0)
        np.save(confidencesPath, tmpArr, allow_pickle=False)
        #print(f'confidences shape (Binary): {tmpArr.shape}')
        #print(f'dataPacket saved (Binary): {tmpArr}')   
    else: 
        np.save(confidencesPath, confidences, allow_pickle=False)
        #print(f'dataPacket shape (Binary): {trainingData.shape}')
        #print(f'dataPacket saved (Binary): {trainingData}')

    #print(f'Confidences: {confidences}') 

    predictionsPath = pathPreface + "/predictions.npy"
    predictions = model.output_layer_activation.predictions(confidences)
    #print(f'Current Prediction: {predictions}')
    #print(f'Current Prediction: {predictions[0]}')

    predList = []
    index = 0
    for prediction in predictions:
        predList.append(prediction)
        #print(f'Prediction loop: {prediction}')
        index += 1

    if confidences[0, predList[0]] < 0.9:  #default to no movement unless 90% confident
        predList[0] = 0

    #print(f'Current Prediction: {predictions}')
    #Write predictions to binary
    if os.path.exists(predictionsPath):
        tmpArr = np.load(predictionsPath,allow_pickle=False)## Gets caughtup here
        #print(f'Predictions from file shape: {tmpArr.shape()}')
        #print(f'Predictions from file: {tmpArr}')
        tmpArr = np.append(tmpArr,predList, axis=0)
        np.save(predictionsPath, tmpArr, allow_pickle=False)
        #print(f'dataPacket shape (Binary): {tmpArr.shape}')
        #print(f'dataPacket saved (Binary): {tmpArr}')   
    else: 
        np.save(predictionsPath, predList, allow_pickle=False)
        #print(f'dataPacket shape (Binary): {predList.shape}')
        #print(f'dataPacket saved (Binary): {predList}')

    predictionStopMS = int(time.time() * 1000)
    predictionTimeMS = predictionStopMS - predictionStartMs


    print(f'Time to predict: {predictionTimeMS}')
    print('*******************************************')
    print(f'prediction final: {predList[0]}') 
    print(f'prediction final: {predList[0]}') 
    print(f'prediction final: {predList[0]}') 
    print('*******************************************')

    #print(f'packet after prediction: {packetData}')

    return predList

def trainOrientation(pathPreface, pathList, packetSize, numSensors, numGestures):
    #Create Dataset
    #TODO: Create data and validation arrays
        # X Data is a randomized 1D array of features in groups of 15 (3 axis * 5 samples)
        # y ground truth is the list of the classes of the data - see spiral_data as an example
    #X,y = spiral_data(samples=1000, classes=3)
    #X_test, y_test = spiral_data(samples=100, classes=3)

    print()
    print('trainOrientation()')
    print(f'pathPreface: {pathPreface}')

    dataPathList = pathList.copy()
    truthPathList = pathList.copy()
    for i in range(len(dataPathList)):
        dataPathList[i] = pathPreface + '/' + dataPathList[i] + ".npy"

    print(f'data Paths: {dataPathList}')  
    
    for i in range(len(truthPathList)):
        truthPathList[i] = pathPreface + '/' +  truthPathList[i] + "_truth.npy"

    print(f'truth Paths: {truthPathList}')  
    
    X,y = getAccDataBinary(dataPathList, truthPathList, packetSize=packetSize, numSensors=numSensors)

    print()
    print(f'truths array for model: {y}') 
    print(f'data array for model: {X}') 
    #y = y.reshape(y.shape[0])  #reshape truth data only if truth data is formatted as 2-D
    EPOCHS = 100
    BATCH_SIZE = 1
    
    modelOk = 0
    if os.path.exists(pathPreface +  "/model.model"):     #Use the existing model if it exists
        model = Model.load(pathPreface + "/model.model")

        try:
            model.finalize()
            print(f'Using exisiting model at: {pathPreface}/model.model') 
            modelOk = 1
        except:
            print('Model file not valid. Creating new model')


    if modelOk == 0:   
        print('Creating a new model')                                 #Or create a new one
        model = Model()   #Instanstiate the model

        #Add layers
        #Input is 15 features (3 Axis * 5 samples)
        model.add(Layer_Dense(3*packetSize * numSensors,300, weight_regularizer_l2=5e-4, bias_regularizer_l2=5e-4))
        model.add(Activation_ReLu())
        model.add(Layer_Dropout(0.1))
        model.add(Layer_Dense(300,numGestures))
        model.add(Activation_Softmax())
        
        model.set(
            loss=Loss_CategoricalCrossEntropy(),
            optimizer=Optimizer_Adam(learning_rate=0.05, decay=5e-5),
            accuracy=Accuracy_Categorical()
        )
        
        model.finalize()
    
    #model.train(X,y, validation_data=(X_test, y_test),epochs=EPOCHS, batch_size=BATCH_SIZE, print_every=5)
    model.train(X,y, epochs=EPOCHS, batch_size=BATCH_SIZE, print_every=1000)
    
    #parameters = model.get_parameters()
    #print(f'parameters: {parameters}')
    
    model.save(pathPreface + "/model.model")

def createTestModel():
    model = Model()   #Instanstiate the model
        
    #Add layers
    #Input is 15 features (3 Axis * 5 samples)
    model.add(Layer_Dense(6,300, weight_regularizer_l2=5e-4, bias_regularizer_l2=5e-4))
    model.add(Activation_ReLu())
    model.add(Layer_Dropout(0.1))
    model.add(Layer_Dense(300,1))
    model.add(Activation_Softmax())
    
    model.set(
        loss=Loss_CategoricalCrossEntropy(),
        optimizer=Optimizer_Adam(learning_rate=0.05, decay=5e-5),
        accuracy=Accuracy_Categorical()
    )
    
    model.finalize()
    model.save('data/test/model.model')




##########################################################################################################
##########################################################################################################
##########################################################################################################
###########################   Neural Network Training and Prediction Examples    #########################
##########################################################################################################
##########################################################################################################
##########################################################################################################



# def RegressionNoValid():
#     #Create Dataset
#     X, y = sine_data()
    
#     #Instanstiate the model
#     model = Model()
    
#     #Add layers
#     model.add(Layer_Dense(1,64))
#     model.add(Activation_ReLu())
#     model.add(Layer_Dense(64,64))
#     model.add(Activation_ReLu())
#     model.add(Layer_Dense(64,1))
#     model.add(Activation_Linear())
    
#     model.set(
#         loss=Loss_MeanSquaredError(),
#         optimizer=Optimizer_Adam(learning_rate=0.005, decay=1e-3),
#         accuracy=Accuracy_Regression()
#     )
    
#     # Finalize the model
#     model.finalize()
    
#     model.train(X, y, epochs=10000, print_every=100)
    
# def binaryLogisticValid():
#     #Create Dataset
#     X,y = spiral_data(samples=100, classes=2)
#     X_test, y_test = spiral_data(samples=100, classes=2)
    
#     y = y.reshape(-1, 1)
#     y_test = y_test.reshape(-1, 1)
    
#     #Instanstiate the model
#     model = Model()
    
#     #Add layers
#     model.add(Layer_Dense(2,64, weight_regularizer_l2=5e-4, bias_regularizer_l2=5e-4))
#     model.add(Activation_ReLu())
#     model.add(Layer_Dense(64,1))
#     model.add(Activation_Sigmoid())
    
#     model.set(
#         loss=Loss_BinaryCrossentropy(),
#         optimizer=Optimizer_Adam(decay=1e-7),
#         accuracy=Accuracy_Categorical()
#     )
    
#     model.finalize()
    
#     model.train(X,y, validation_data=(X_test, y_test),epochs=10000, print_every=100)
    
# def CategoricalCrossEntropy():
#     #Create Dataset
#     X,y = spiral_data(samples=1000, classes=3)
#     X_test, y_test = spiral_data(samples=100, classes=3)
    
#     #Instanstiate the model
#     model = Model()
    
#     #Add layers
#     model.add(Layer_Dense(2,512, weight_regularizer_l2=5e-4, bias_regularizer_l2=5e-4))
#     model.add(Activation_ReLu())
#     model.add(Layer_Dropout(0.1))
#     model.add(Layer_Dense(512,3))
#     model.add(Activation_Softmax())
    
#     model.set(
#         loss=Loss_CategoricalCrossEntropy(),
#         optimizer=Optimizer_Adam(learning_rate=0.05, decay=5e-5),
#         accuracy=Accuracy_Categorical()
#     )
    
#     model.finalize()
    
#     model.train(X,y, validation_data=(X_test, y_test),epochs=10000, print_every=100)
    
# def batchModel():
#     #Create Dataset
#     X,y = spiral_data(samples=1000, classes=3)
#     X_test, y_test = spiral_data(samples=100, classes=3)
    
#     EPOCHS = 1000
#     BATCH_SIZE = 250
    
#     #Instanstiate the model
#     model = Model()
    
#     #Add layers
#     model.add(Layer_Dense(2,512, weight_regularizer_l2=5e-4, bias_regularizer_l2=5e-4))
#     model.add(Activation_ReLu())
#     model.add(Layer_Dropout(0.1))
#     model.add(Layer_Dense(512,3))
#     model.add(Activation_Softmax())
    
#     model.set(
#         loss=Loss_CategoricalCrossEntropy(),
#         optimizer=Optimizer_Adam(learning_rate=0.05, decay=5e-5),
#         accuracy=Accuracy_Categorical()
#     )
    
#     model.finalize()
    
#     model.train(X,y, validation_data=(X_test, y_test),epochs=EPOCHS, batch_size=BATCH_SIZE, print_every=5)
    
#     parameters = model.get_parameters()
#     print(parameters)
    
#     model.save('data/model00.model')
    
# def testLoadModel():
#     #Create Dataset
#     X,y = spiral_data(samples=1000, classes=3)
#     X_test, y_test = spiral_data(samples=100, classes=3)
    
#     model = Model.load('data/model00.model')
    
#     model.evaluate(X_test, y_test)
    
# def prediction():
#     #Create Dataset
#     X,y = spiral_data(samples=1000, classes=3)
#     X_test, y_test = spiral_data(samples=100, classes=3)
    
#     model = Model.load('data/model00.model')
    
#     confidences = model.predict(X_test[:5])
#     predictions = model.output_layer_activation.predictions(confidences)
#     print(predictions)



# def AccModel01():
#     #Create Dataset
#     #TODO: Create data and validation arrays
#         # X Data is a randomized 1D array of features in groups of 15 (3 axis * 5 samples)
#         # y ground truth is the list of the classes of the data - see spiral_data as an example
#     #X,y = spiral_data(samples=1000, classes=3)
#     #X_test, y_test = spiral_data(samples=100, classes=3)
    
#     X,y = getAccDataBinary(["data\packet5Avg20\\training00_noMove.npy","data\packet5Avg20\\training01_upandDown.npy","data\packet5Avg20\\training02_inandOut.npy"], ["data\packet5Avg20\\training00_noMove_truth.npy","data\packet5Avg20\\training01_upandDown_truth.npy","data\packet5Avg20\\training02_inandOut_truth.npy"])
#     #y = y.reshape(y.shape[0])  #reshape truth data only if truth data is formatted as 2-D
#     EPOCHS = 500
#     BATCH_SIZE = 1
    
#     #Instanstiate the model
#     model = Model()
    
#     #Add layers
#     #Input is 15 features (3 Axis * 5 samples)
#     model.add(Layer_Dense(30,150, weight_regularizer_l2=5e-4, bias_regularizer_l2=5e-4))
#     model.add(Activation_ReLu())
#     model.add(Layer_Dropout(0.1))
#     model.add(Layer_Dense(150,3))
#     model.add(Activation_Softmax())
    
#     model.set(
#         loss=Loss_CategoricalCrossEntropy(),
#         optimizer=Optimizer_Adam(learning_rate=0.05, decay=5e-5),
#         accuracy=Accuracy_Categorical()
#     )
    
#     model.finalize()
    
#     #model.train(X,y, validation_data=(X_test, y_test),epochs=EPOCHS, batch_size=BATCH_SIZE, print_every=5)
#     model.train(X,y, epochs=EPOCHS, batch_size=BATCH_SIZE, print_every=1000)
    
#     parameters = model.get_parameters()
#     #print(f'parameters: {parameters}')
    
#     model.save('data/AccModel01')

# def Acc01prediction():
#     #Create Dataset
#     X,y = getAccDataBinary(["data\packet5Avg20\\training00_noMove.npy","data\packet5Avg20\\training01_upandDown.npy","data\packet5Avg20\\training02_inandOut.npy"], ["data\packet5Avg20\\training00_noMove_truth.npy","data\packet5Avg20\\training01_upandDown_truth.npy","data\packet5Avg20\\training02_inandOut_truth.npy"])
   
#     model = Model.load('data/AccModel01')
    
#     confidences = model.predict(X)
#     predictions = model.output_layer_activation.predictions(confidences)
#     print(predictions)


# def convertTruthBinary(truthPathList):
#     #One time function to convert truth data to a 1-D array - done automatically in socketClient from now on
#     for path in truthPathList:
#         if os.path.exists(path):
#             # print("****")
#             # print(path)
#             y = np.load(path,allow_pickle=False)
#             print(y)
#             print(y.shape)
#             y = y.reshape(y.shape[0])  #reshape truth data only if truth data is formatted as 2-D
#             print(y)
#             print(y.shape)
#             np.save(path, y, allow_pickle=False)
#     for path in truthPathList:   #Check that the file was written to properly
#         if os.path.exists(path):
#            y = np.load(path,allow_pickle=False)
#           print(y)
#           print(y.shape)



# def train3Gestures(pathPreface):
#     #Create Dataset
#     #TODO: Create data and validation arrays
#         # X Data is a randomized 1D array of features in groups of 15 (3 axis * 5 samples)
#         # y ground truth is the list of the classes of the data - see spiral_data as an example
#     #X,y = spiral_data(samples=1000, classes=3)
#     #X_test, y_test = spiral_data(samples=100, classes=3)
    
#     X,y = getAccDataBinary([pathPreface + "noMove.npy", pathPreface + "upandDown.npy", pathPreface + "inandOut.npy"], [pathPreface + "noMove_truth.npy", pathPreface + "upandDown_truth.npy", pathPreface + "inandOut_truth.npy"])
#     #y = y.reshape(y.shape[0])  #reshape truth data only if truth data is formatted as 2-D
#     EPOCHS = 500
#     BATCH_SIZE = 1
    
#     #Instanstiate the model
#     model = Model()
    
#     #Add layers
#     #Input is 15 features (3 Axis * 5 samples)
#     model.add(Layer_Dense(30,150, weight_regularizer_l2=5e-4, bias_regularizer_l2=5e-4))
#     model.add(Activation_ReLu())
#     model.add(Layer_Dropout(0.1))
#     model.add(Layer_Dense(150,3))
#     model.add(Activation_Softmax())
    
#     model.set(
#         loss=Loss_CategoricalCrossEntropy(),
#         optimizer=Optimizer_Adam(learning_rate=0.05, decay=5e-5),
#         accuracy=Accuracy_Categorical()
#     )
    
#     model.finalize()
    
#     #model.train(X,y, validation_data=(X_test, y_test),epochs=EPOCHS, batch_size=BATCH_SIZE, print_every=5)
#     model.train(X,y, epochs=EPOCHS, batch_size=BATCH_SIZE, print_every=1000)
    
#     parameters = model.get_parameters()
#     #print(f'parameters: {parameters}')
    
#     model.save(pathPreface + "model")



# def main():
#     #createTestModel()

# #     #RegressionNoValid()
# #     #binaryLogisticValid()
# #     #CategoricalCrossEntropy()
# #     #batchModel()
# #     #testLoadModel()
# #     #prediction()
# #     # X,y = spiral_data(samples=1000, classes=3)
# #     # print(X)
# #     # print(y)
# #     #getAccData(["data\packet5Avg20/\/training00_noMove.npy","data\packet5Avg20\/training01_upandDown.npy","data\packet5Avg20\/training02_inandOut.npy"])
# #     #dataArr, truthArr = getAccDataCSV(['data\packet5Avg20\\training00_noMove.csv',"data\packet5Avg20\\training01_upandDown.csv","data\packet5Avg20\\training02_inandOut.csv"], ['data\packet5Avg20\\training00_noMove_truth.csv',"data\packet5Avg20\\training01_upandDown_truth.csv","data\packet5Avg20\\training02_inandOut_truth.csv"])
# #     #dataArrBin, truthArrBin = getAccDataBinary(["data\packet5Avg20\\training00_noMove.npy","data\packet5Avg20\\training01_upandDown.npy","data\packet5Avg20\\training02_inandOut.npy"], ["data\packet5Avg20\\training00_noMove_truth.npy","data\packet5Avg20\\training01_upandDown_truth.npy","data\packet5Avg20\\training02_inandOut_truth.npy"])
# #     #AccModel01()
# #     #Acc01prediction()
# #     #convertTruthCSV(["data\packet5Avg20\\training00_noMove_truth.csv","data\packet5Avg20\\training01_upandDown_truth.csv","data\packet5Avg20\\training02_inandOut_truth.csv"])

# #     #convertPickletoDill()

# if __name__ == "__main__": main()