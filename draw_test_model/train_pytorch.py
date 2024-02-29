import torch
import torchvision
from torch import nn
from torchvision import datasets
from torchvision.transforms import v2

import matplotlib.pyplot as plt
import numpy as np
import numpy.random as rand

import datetime

#####################################################################
# AUXILLIARY

def log(l: str) -> str:
    print(l)
    return l + "\n"


#####################################################################
# TRAINING LIST AND OPTIONS

# Format: the dataset, the model, the number of epochs, save model/results
trainList = [
#    {'data': 'digits', 'model': 'dense2', 'opt': 'adam', 'epochs': 1, 'save': True},
#    {'data': "digits", 'model': "conv2", 'opt': 'adam', 'epochs': 1, 'save': True},
#    {'data': 'fashion', 'model': 'dense2', 'opt': 'adam', 'epochs': 5, 'save': True},
    {'data': "fashion", 'model': "conv2", 'opt': 'adam', 'epochs': 20, 'save': True},
    ]


#####################################################################
# SOME UNIFORM OPTIONS

device = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)


#####################################################################
# THE MODELS

class Dense2(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.reset_parameters = initWeights                 # Initialization (does this actually work????  i.e. does it apply it to the stuff below>???)
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28*28, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(p=0.5),
            nn.Linear(256, 10)
        )
    

    def rescale(self, x):
        return x / 255.
    
    def unrescale(self, x):
        return x * 255.    

    def forward(self, x):
        x = self.flatten(x)
        logits = self.linear_relu_stack(x)
        return logits


class Conv2(nn.Module):             # Input shape (1, 28, 28) or (BATCH SIZE, 1, 28, 28)
    def __init__(self):
        super().__init__()
        # How to do initialization?
        self.convolution_stack = nn.Sequential(
            nn.Conv2d(1, 32, (3,3), padding='same'),                    # Input channel 1, output 32, filter size (3,3)
            nn.ReLU(),
            nn.MaxPool2d((2,2)),    # Image now 14x14
            nn.Dropout(p=0.2),
            nn.BatchNorm2d(32),
            nn.Conv2d(32, 64, (3,3), padding='same'),
            nn.ReLU(),
            nn.MaxPool2d((2,2)),    # Image now 7x7
            nn.Dropout(p=0.2),
            nn.BatchNorm2d(64),
            nn.Flatten(),           # Default start_dim=1
            nn.Linear(7*7*64, 128),
            nn.ReLU(),
            nn.Dropout(p=0.5),
            nn.BatchNorm1d(128),
            nn.Linear(128, 10)
        )

    def rescale(self, x):
        return x / 255.
    
    def unrescale(self, x):
        return x * 255.  

    def addChannels(self, x, n=1):
        return torch.reshape(list(x.shape)[:-2] + [n] + list(x.shape)[-2:])
    
    def randomWiggle(self, x):
        zoom = rand.exponential(scale=1.0)                                              # Probability of no zoom is 1 - e^(-scale) 
        if zoom > 1.:
            x = v2.functional.affine(scale=1./zoom)(x)                                          # Maybe select the zoom from some distribution?
        rot = rand.exponential(scale=0.3) * np.sign(rand.uniform(-1, 1))                # Want 95% of zooms to between [-10, 10], so want 1 - e^(-10 * scale) roughly 95%
        x_trans = rand.exponential(scale=max(zoom, 1.)) (np.sign(rand.uniform(-1,1)))     # Depends on zoom.  With no zoom, 95% of translates up to 3. 
        y_trans = rand.exponential(scale=max(zoom, 1.)) (np.sign(rand.uniform(-1,1)))
        x = v2.functional.affine(degrees=rot, translate=[x_trans, y_trans])(x)
        return x 

    def forward(self, x):
        logits = self.convolution_stack(x)
        return logits


#####################################################################
# INITIALIZER, LOSS FUNCTION, BATCH SIZE

# Weight initializer
def initWeights(m):
    if isinstance(m, nn.Linear):
        torch.nn.init.kaiming_uniform_(m.weight)                # I guess there's not a huge difference between uniform vs. normal, and uniform probably easier to sample
        if self.bias is not None:                               # Set the linear bias (just copied it from default nn.Linear code but can tweak it here)
            fan_in, _ = init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
            init.uniform_(self.bias, -bound, bound)
        #m.bias.data.fill_(0.01)                                # E.g. if I just want to set it to something.

# Loss function
loss_fn, loss_fn_name = nn.CrossEntropyLoss(), "nll"                   # Inputs are logits (i.e. pre-softmax)
#loss_fn, loss_fn_name = torch.nn.HingeEmbeddingLoss(margin=1.), "hinge"        

# Batch size (i.e. how often back-propagation happens)
batch_size = 64


#####################################################################
# DATA AND FEATURE TRANSFORMATIONS

# Feature transformation TODO
class RandomWiggle(v2.Transform):
    
    def __init__(self):
        super().__init__()


    def _transform(self, x):
        zoom = rand.exponential(scale=1.0)                                              # Probability of no zoom is 1 - e^(-scale) 
        if zoom > 1.:
            x = v2.functional.affine(scale=1./zoom)(x)                                          # Maybe select the zoom from some distribution?
        rot = rand.exponential(scale=0.3) * np.sign(rand.uniform(-1, 1))                # Want 95% of zooms to between [-10, 10], so want 1 - e^(-10 * scale) roughly 95%
        x_trans = rand.exponential(scale=max(zoom, 1.)) (np.sign(rand.uniform(-1,1)))     # Depends on zoom.  With no zoom, 95% of translates up to 3. 
        y_trans = rand.exponential(scale=max(zoom, 1.)) (np.sign(rand.uniform(-1,1)))
        x = v2.functional.affine(degrees=rot, translate=[x_trans, y_trans])(x)
        return x 


# ToTensor transforms to tensor of the form (BATCH SIZE, 1, 28, 28) with values in range [0, 1]
digitsTrainData = datasets.MNIST(
    root="data",
    train=True,
    download=True,
    transform=v2.Compose([v2.RandomAffine(10, translate=(.3,.3), scale=(.75, 1.)), torchvision.transforms.ToTensor()]),
)
digitsTestData = datasets.MNIST(
    root="data",
    train=False,
    download=True,
    transform=torchvision.transforms.ToTensor(),
)
digitsTrainLoader = torch.utils.data.DataLoader(digitsTrainData, batch_size=batch_size)
digitsTestLoader = torch.utils.data.DataLoader(digitsTestData, batch_size=batch_size)


fashionTrainData = datasets.FashionMNIST(
    root="data",
    train=True,
    download=True,
    transform=v2.Compose([v2.RandomAffine(10, translate=(.3,.3), scale=(.75, 1.)), torchvision.transforms.ToTensor()]),
)
fashionTestData = datasets.FashionMNIST(
    root="data",
    train=False,
    download=True,
    transform=torchvision.transforms.ToTensor(),            # Check maybe this already has the extra channel???
)
fashionTrainLoader = torch.utils.data.DataLoader(fashionTrainData, batch_size=batch_size)
fashionTestLoader = torch.utils.data.DataLoader(fashionTestData, batch_size=batch_size)



#####################################################################
# TRAIN, TEST, SAVE


# Now actually train the models and save the results
for d in trainList:
    logtext = ""
    logtext += log(f"Using {device} device")

    # Load the relevant data
    if d['data'] == "digits":
        train, test = digitsTrainLoader, digitsTestLoader
    elif d['data'] == "fashion":
        train, test = fashionTrainLoader, fashionTestLoader
    else:
        print("Data", d['data'], "not found!  Exiting.")
        exit()
    logtext += log(f"Training dataset and transforms: {train.dataset}")
    logtext += log(f"Validation dataset and transforms: {test.dataset}")
    logtext += log(f"Batch size: {batch_size}")

    # Load the specified model
    if d['model'] == "dense2":
        m = Dense2()
    elif d['model'] == "conv2":
        m = Conv2()
    else:
        print("Model", d['model'], "not found!  Exiting.")
        exit()
    logtext += log("Loaded model:")
    logtext += log(str(m))

    # Make the name
    name = d['data'] + "." + d['model'] + "." + loss_fn_name + "." + d['opt'] + "." + str(d['epochs']) + "." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Define optimizer on the model (m.parameters() is iterator over parameters)
    if d['opt'] == 'sgd':
        optimizer = torch.optim.SGD(m.parameters(), lr=1e-3, dampening=0, momentum=0, weight_decay=0)                    # lr = learning rate
    elif d['opt'] == 'adam':
        optimizer, optimizer_name = torch.optim.Adam(m.parameters(), lr = 1e-3), "adam"
    else:
        print("Optimizer", d['opt'], "not found!  Exiting.")
        exit()
    logtext += log("Loaded optimizer:")
    logtext += log(str(optimizer))

    # Record accuracy and loss for testing and training in each epoch
    trainLoss = []
    trainAcc = []
    testLoss = []
    testAcc = []
    for ep in range(0, d['epochs']):
        logtext += log("Epoch " + str(ep + 1) + "/" + str(d['epochs']) + ": -------------------------------------")

        logtext += log("Training: " + name)
        m.train()           # Sets in training mode, e.g. vs. m.eval()
        
        train_loss = 0.
        train_correct = 0.
        for curBatch, (X, y) in enumerate(train):
            X, y = X.to(device), y.to(device)

            pred = m(X)                     # Output is a tensor with gradient functions (and knows about m)
            loss = loss_fn(pred, y)         # Also a tensor with gradient functions

            loss.backward()                 # Computes the gradients (now stored in the tensors in the model m)
            optimizer.step()                # Performs an optimization step for the tensors in the model m
            optimizer.zero_grad()           # Zeroes out computed gradients in m

            train_loss += loss.item()
            train_correct += (pred.argmax(1) == y).type(torch.float).sum().item()
            trainsize = len(train.dataset)

            if curBatch % 100 == 0:         # Print some information every 100 batches
                loss, current = loss.item(), (curBatch + 1) * batch_size
                logtext += log(f"loss: {loss:>7f}  [{current:>5d}/{trainsize:>5d}]")

        # Log the training accuracy and loss
        train_loss /= len(train)
        train_acc = train_correct / trainsize
        trainLoss.append(train_loss)
        trainAcc.append(train_acc)
        
        logtext += log("Testing: " + name)
        m.eval()
        test_loss, correct = 0.,0
        with torch.no_grad():
            for X, y in test:
                X, y = X.to(device), y.to(device)
                pred = m(X)
                test_loss += loss_fn(pred, y).item()
                correct += (pred.argmax(1) == y).type(torch.float).sum().item()     # argmax returns a vector whose nth entry is the maximum index in the nth row
            
            testsize = len(test.dataset)
            test_loss /= len(test)
            test_acc = correct / testsize
            logtext += log(f"Test Error: \n Accuracy: {(test_acc*100):>0.1f}%, Avg loss: {test_loss:>8f} \n")
        testLoss.append(test_loss)
        testAcc.append(test_acc)



    logtext += log("Done training and testing!")

    # Log the accuracy and loss across all epochs
    logtext += log("Training accuracy: " + str(trainAcc))
    logtext += log("Training loss: " + str(trainLoss))
    logtext += log("Validation accuracy: " + str(testAcc))
    logtext += log("Validation loss: " + str(testLoss))
    
    # Plot some graphs
    epochs_range = range(d['epochs'])
    plt.figure(figsize=(8, 8))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, trainAcc, label='Training Accuracy')
    plt.plot(epochs_range, testAcc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Training and Validation Accuracy')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, trainLoss, label='Training Loss')
    plt.plot(epochs_range, testLoss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss')
    #plt.show()        

    if d['save'] == True:
        #torch.save(m.state_dict(), name + ".pth")
        plt.savefig("models/" + name + ".pth.png")
        logtext += log("Saved accuracy/loss plot to " + name + ".pth.png")
        model_scripted = torch.jit.script(m)
        model_scripted.save("models/" + name + ".pth")
        logtext += log("Saved PyTorch model to " + name + ".pth")
        with open("models/" + name + ".pth.log", "w") as f:
            logtext += log("Saved logs to " + name + ".pth.log")
            f.write(logtext)
            