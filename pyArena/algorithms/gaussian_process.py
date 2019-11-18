import numpy as np
from ..core import utils

"""
Class that implements a standard GP regression. Suitable for smaller problems.
Necessary input is the kernel function.
"""
class GPRegression:

    def __init__(self, **kwargs):

        if 'kernel' not in kwargs:
            raise KeyError("Must specify a kernel function!")
        else:
            self.kernel = kwargs['kernel']

        if 'mean' not in kwargs:
            self.meanFunc = lambda x: 0
        else:
            self.meanFunc = kwargs['mean']

        if 'measurementNoiseCov' not in kwargs:
            self.noiseCov = 0.0
        else:
            self.noiseCov = kwargs['measurementNoiseCov']

        self.trainingData = utils.Structure()
        self.priorMean = utils.Structure()
        self.priorCovariance = utils.Structure()

    """
    train_offline(inpTrain, outTrain)
    The function is used to train the GP model given input (inpTrain) and  output (outTrain) training data.

    Function arguments:
    inpTrain - (numDim, numTrain) numpy array
    outTrain - (numTrain, 1) numpy array. Actually a 1D numpy array
    """
    def train_offline(self, inpTrain, outTrain):

        self.trainingData.inputs = inpTrain.copy()
        self.trainingData.outputs = outTrain.copy()
        self.trainingData.length = len(inpTrain)

        # Step 1: Construct prior mean and covariances

        numTrain = len(inpTrain)

        # Prior Mean initialization
        m_m = np.zeros([numTrain, 1])

        # Prior Covariance initialization
        K_mm = np.zeros([numTrain, numTrain])

        for train_index in range(0, numTrain):
            m_m[train_index] = self.meanFunc(inpTrain[train_index])
            K_mm[train_index, :] = self.kernel(inpTrain[train_index], inpTrain)

        self.priorMean.m_m = m_m
        self.priorCovariance.K_mm = K_mm
        self.priorCovariance.K_mm_inv = np.linalg.inv(K_mm + self.noiseCov * np.eye(numTrain))

    """
    Evaluate GP to obtain mean and variance at a testing point 'at_input' which is (numInputs,numDim) numpy array
    """
    def predict_value(self, at_input):

        # Step 1: Compute the prior mean and covariance matrices
        numTest = len(at_input)
        numTrain = self.trainingData.length

        # Mean
        m_star = self.meanFunc(at_input)
        m_m = self.priorMean.m_m

        # Covariances
        K_star_m = np.zeros([numTest,numTrain])
        for inp_index in range(0,numTest):
            K_star_m[inp_index,:] = self.kernel(at_input[inp_index], self.trainingData.inputs)

        K_mm_inv = self.priorCovariance.K_mm_inv
        K_star_star = np.zeros([numTest,numTest])
        for i in range(0,numTest):
            for j in range(i, numTest):
                K_star_star[i,j] = self.kernel(at_input[i], at_input[j])
                K_star_star[j,i] = K_star_star[i,j]

        # Step 2: Predict - get posterior mean and covariance
        mu_star = m_star + K_star_m @ K_mm_inv @ (self.trainingData.outputs - m_m)
        Sigma_star_star = K_star_star - K_star_m @ K_mm_inv @ K_star_m.T

        return mu_star, Sigma_star_star

    """
    trainModelIterative(inpTrain, outTrain) 
    The function is used to train the GP model given input (inpTrain) and  output (outTrain) training data iteratively.
    The input and output training data is stored. Training is performed only when the trainingFlag is active
    Training the GP model implies computation of prior mean and convariance distribution over the regressor function.

    Necessary function arguments:
    inpTrain - (numDim, 1) numpy array
    outTrain - 1 float
    trainingFlag - bool. 0 - do not train (only store new data). 1 - store and train
    """
    #TODO: Consider removal - might not be useful!
    def trainGPIterative(self, inpTrain, outTrain, trainingFlag):
        self.numTrain = len(self.yTrain) + 1

        self.yTrain =  np.append(self.yTrain, outTrain)

        self.xTrain = np.append(self.xTrain, inpTrain)
        self.xTrain = self.xTrain.reshape([self.numTrain, 2])
   
        if(trainingFlag==False):
            return

        # Compute the prior GP covariance matrix
        Ktrtr = np.zeros([self.numTrain,self.numTrain])
        self.inpTrain = self.xTrain.T
        self.outTrain = self.yTrain

        for row in range(0,self.numTrain):
            for column in range(row,self.numTrain):
                Ktrtr[column, row] = Ktrtr[row, column] = self.kernel(self.inpTrain[:,row],self.inpTrain[:,column])
        self.priorCovariance = Ktrtr


"""
FITCSparseGP - Fully Independent Training Conditional Sparse GP Regression
This class implements FITC Sparse GP regression. Necessary inputs are
kernel - a kernel needs to be specified. Example: Squared exponential kernel
measurementNoiseCov - an estimate of the covariance of the noise. Usually a zero mean gaussian distribution.
Note: The current implementation assumed zero mean GPs  
"""
class FITCSparseGP:

    def __init__(self, **kwargs):

        # super().__init__(**kwargs)

        if 'kernel' not in kwargs:
            raise KeyError("Must specify a kernel function!")
        else:
            self.kernel = kwargs['kernel']

        if 'mean' not in kwargs:
            self.meanFunc = lambda x: 0
        else:
            self.meanFunc = kwargs['mean']

        if 'measurementNoiseCov' not in kwargs:
            self.noiseCov = 0.0
        else:
            self.noiseCov = kwargs['measurementNoiseCov']

        self.inducingData = utils.Structure()
        self.trainingData = utils.Structure()

        self.priorMean = utils.Structure()
        self.priorCovariance = utils.Structure()

        self.posteriorMean = utils.Structure()
        self.posteriorCovariance = utils.Structure()

    # End of __init__ function

    def inv(self, inpMatrix, mode='np.linalg'):

        if mode == 'np.linalg':
            matrix = np.linalg.inv(inpMatrix)

        return matrix

    def train_offline(self, inpTrain, outTrain, inpInduce):

        self.trainingData.inputs = inpTrain.copy()
        self.trainingData.outputs = outTrain.copy()
        self.inducingData.inputs = inpInduce.copy()

        self.trainingData.length = len(inpTrain)
        self.inducingData.length = len(inpInduce)

        # Step 1: Construct prior mean and covariances

        numTrain = len(inpTrain)
        numInduce = len(inpInduce)

        # Prior Mean
        m_m = np.zeros([numTrain, 1])
        m_u = np.zeros([numInduce, 1])

        # Prior Covariances
        K_mm = np.zeros([numTrain, numTrain])
        K_mu = np.zeros([numTrain, numInduce])
        K_uu = np.zeros([numInduce, numInduce])

        for train_index in range(0, numTrain):
            m_m[train_index] = self.meanFunc(inpTrain[train_index])
            K_mm[train_index, :] = self.kernel(inpTrain[train_index], inpTrain)
            K_mu[train_index, :] = self.kernel(inpTrain[train_index], inpInduce)

        for induce_index in range(0, numInduce):
            m_u[induce_index] = self.meanFunc(inpInduce[induce_index])
            K_uu[induce_index, :] = self.kernel(inpInduce[induce_index], inpInduce)

        self.priorMean.m_m = m_m
        self.priorMean.m_u = m_u

        self.priorCovariance.K_mm = K_mm
        self.priorCovariance.K_uu = K_uu
        self.priorCovariance.K_mu = K_mu
        self.priorCovariance.K_uu_inv = self.inv(K_uu)

        # Step 2: Compute posterior mean and covariances using FITC assumption

        K_uu_inv = self.priorCovariance.K_uu_inv

        Epsilon_mm = self.noiseCov * np.eye(numTrain)
        Lambda_mm = np.diag(np.diag(K_mm - K_mu @ K_uu_inv @ K_mu.T))
        Lambda_Epsilon_inv = self.inv(Lambda_mm + Epsilon_mm)

        Delta_uu = K_uu + K_mu.T @ Lambda_Epsilon_inv @ K_mu
        Delta_uu_inv = self.inv(Delta_uu)

        Sigma_mu = Epsilon_mm @ Lambda_Epsilon_inv @ K_mu @ Delta_uu_inv @ K_uu
        Sigma_uu = K_uu @ Delta_uu_inv @ K_uu

        mu_u = m_u + Sigma_mu.T @ self.inv(Epsilon_mm) @ (outTrain - m_m)

        self.posteriorMean.mu_u = mu_u
        self.posteriorCovariance.Sigma_mu = Sigma_mu
        self.posteriorCovariance.Sigma_uu = Sigma_uu

    def train_online(self, **new_measurement):
        pass

    def predict_value(self, at_input):

        # Step 1: Compute the prior mean and covariance matrices

        # Mean
        m_star = self.meanFunc(at_input)
        m_u = self.priorMean.m_u
        mu_u = self.posteriorMean.mu_u

        # Covariances
        K_star_u = self.kernel(at_input, self.inducingData.inputs)
        K_uu_inv = self.priorCovariance.K_uu_inv
        K_star_star = self.kernel(at_input, at_input)
        K_uu = self.priorCovariance.K_uu
        Sigma_uu = self.posteriorCovariance.Sigma_uu

        # Step 2: Predict - get posterior mean and covariance

        mu_star = m_star + K_star_u @ K_uu_inv @ (mu_u - m_u)
        Sigma_star_star = K_star_star - K_star_u @ K_uu_inv @ (K_uu - Sigma_uu) @ K_uu_inv @ K_star_u.T

        return mu_star, Sigma_star_star
