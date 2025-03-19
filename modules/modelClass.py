import torch.nn as nn

class DirectionClassifierNet(nn.Module):
    def __init__(self, input_dim=3, hidden_dim=64, output_dim=11, num_hidden_layers=2):
        super(DirectionClassifierNet, self).__init__()
        layers = []
        layers.append(nn.Linear(input_dim, hidden_dim))
        layers.append(nn.ReLU())

        for _ in range(num_hidden_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())

        layers.append(nn.Linear(hidden_dim, output_dim))

        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)