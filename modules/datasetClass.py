import torch
import torch.utils.data as data

class DirectionDataset(data.Dataset):
    def __init__(self, X, y_int):
        self.X = X
        self.y = y_int

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        X_t = torch.tensor(self.X[idx], dtype=torch.float32)
        y_t = torch.tensor(self.y[idx], dtype=torch.long)
        return X_t, y_t
