import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

# --- 1. The PyTorch Brain ---
class LiveNeuralNet(nn.Module):
    def __init__(self):
        super(LiveNeuralNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(2, 32), nn.ReLU(),
            nn.Linear(32, 32), nn.ReLU(),
            nn.Linear(32, 4)
        )
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.parameters(), lr=0.03)

    def forward(self, x):
        return self.network(x)

    def train_batch(self, inputs, targets):
        self.optimizer.zero_grad()
        predictions = self.forward(inputs)
        loss = self.criterion(predictions, targets)
        loss.backward()
        self.optimizer.step()
        return loss.item(), torch.argmax(predictions[-1]).item()

# --- 2. The Arena Manager ---
class ModelArena:
    def __init__(self):
        self.memory = [] 
        self.active_name = "pytorch"
        
        # Load up all our contestants
        self.pytorch_model = LiveNeuralNet()
        self.tree = DecisionTreeClassifier(max_depth=7)
        self.svm = SVC(kernel="rbf", C=1.0, gamma=10)
        self.knn = KNeighborsClassifier(n_neighbors=3)

    def train_single_point(self, x, y, label):
        self.memory.append((x, y, int(label)))
        return self._retrain()

    def set_model(self, model_name):
        """Swaps the active brain and immediately recalculates everything."""
        self.active_name = model_name
        return self._retrain()

    def _retrain(self):
        """Trains whichever model is currently active."""
        if len(self.memory) == 0:
            return 1.0, 0

        X = [[m[0], m[1]] for m in self.memory]
        Y = [m[2] for m in self.memory]
        
        if self.active_name == "pytorch":
            inputs = torch.tensor(X, dtype=torch.float32)
            targets = torch.tensor(Y, dtype=torch.long)
            loss, latest_pred = self.pytorch_model.train_batch(inputs, targets)
            return loss, (1 if latest_pred == Y[-1] else 0)
        else:
            # Scikit-learn models crash if there is only 1 color on the board.
            # We catch that here and fake a "perfect" score until a 2nd color is clicked.
            if len(set(Y)) < 2:
                return 0.0, 1
            
            # Train the selected sklearn model
            model = getattr(self, self.active_name)
            model.fit(X, Y)
            latest_pred = model.predict([X[-1]])[0]
            # Sklearn models don't calculate "loss" step-by-step like PyTorch, so we return 0.0
            return 0.0, (1 if latest_pred == Y[-1] else 0)

    def get_decision_boundary(self):
        if len(self.memory) == 0:
            return []
            
        grid_size = 50
        x_vals = np.linspace(0, 1, grid_size)
        y_vals = np.linspace(0, 1, grid_size)
        xx, yy = np.meshgrid(x_vals, y_vals)
        grid_points = np.c_[xx.ravel(), yy.ravel()]

        if self.active_name == "pytorch":
            inputs = torch.tensor(grid_points, dtype=torch.float32)
            with torch.no_grad():
                preds = self.pytorch_model(inputs)
                classes = torch.argmax(preds, dim=1).numpy()
        else:
            if len(set(m[2] for m in self.memory)) < 2:
                classes = np.full(grid_size * grid_size, self.memory[0][2])
            else:
                model = getattr(self, self.active_name)
                classes = model.predict(grid_points)

        return classes.reshape(grid_size, grid_size).tolist()

    def reset(self):
        self.memory = []
        self.pytorch_model = LiveNeuralNet() 