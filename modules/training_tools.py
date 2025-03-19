import os
import random
import numpy as np
import pandas as pd
import json

import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data

from sklearn.preprocessing import label_binarize, LabelEncoder
from torch.optim.lr_scheduler import ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_recall_fscore_support,
    roc_auc_score
)

from modules.datasetClass import DirectionDataset
from modules.modelClass import DirectionClassifierNet

CSV_FILE           = "data/robot_data_v2.csv"
SAVE_MODEL_PATH    = "models/best_model.pth"
SAVE_CLASSES_JSON  = "models/classes.json"
SEED               = 42
TEST_SIZE          = 0.2
NUM_EPOCHS         = 50
PATIENCE           = 5
BATCH_SIZE         = 64
LEARNING_RATE      = 1e-3

HIDDEN_DIM         = 64
NUM_HIDDEN_LAYERS  = 2

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def load_classification_data(csv_file):
    """
    We assume columns:
      timestamp, L_distance, M_distance, R_distance, light1, light2,
      line_sensors, motor1, motor2, motor3, motor4, direction

    We'll drop everything except [L_distance, M_distance, R_distance, direction].
    'direction' is our label, 'L_distance/M_distance/R_distance' are our features.
    """
    df = pd.read_csv(csv_file)

    drop_cols = ["timestamp", "light1", "light2", "line_sensors",
                 "motor1", "motor2", "motor3", "motor4"]
    for c in drop_cols:
        if c in df.columns:
            df.drop(columns=[c], inplace=True, errors='ignore')

    required_inputs = ["L_distance", "M_distance", "R_distance"]
    for col in required_inputs + ["direction"]:
        if col not in df.columns:
            raise ValueError(f"CSV missing column '{col}' in {csv_file}")

    X = df[required_inputs].to_numpy().astype(np.float32)
    directions_str = df["direction"].astype(str).to_list()

    return X, directions_str

def compute_classification_metrics(model, data_loader, device, num_classes):
    """
    Returns macro-averaged (precision, recall, f1).
    Also calculates macro-averaged multi-class AUC if possible.
    """
    model.eval()
    all_preds = []
    all_targets = []
    all_probs = []

    softmax = nn.Softmax(dim=1)

    with torch.no_grad():
        for batch_x, batch_y in data_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            logits = model(batch_x)
            probs = softmax(logits)    

            preds = torch.argmax(logits, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    all_probs = np.array(all_probs)

    precision, recall, f1, _ = precision_recall_fscore_support(
        all_targets, all_preds, average='macro', zero_division=0
    )

    if num_classes > 2:
        all_targets_1hot = label_binarize(all_targets, classes=np.arange(num_classes))
        try:
            auc_macro = roc_auc_score(
                all_targets_1hot, all_probs,
                multi_class='ovr', average='macro'
            )
        except ValueError:
            auc_macro = float('nan')
    else:
        auc_macro = float('nan')

    metrics = {
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "auc_macro": auc_macro
    }
    return metrics

def train_model_classification(
    model,
    train_loader,
    val_loader,
    criterion=nn.CrossEntropyLoss(),
    optimizer=None,
    scheduler=None,
    num_epochs=50,
    patience=5,
    device='cpu',
    num_classes=10
):
    """
    We'll do early stopping based on best macro-F1 from validation set.
    We'll log train loss each epoch, ignoring accuracy for unbalanced data.
    """
    if optimizer is None:
        optimizer = optim.Adam(model.parameters(), lr=1e-3)

    best_val_f1 = 0.0
    best_model_state = None
    patience_counter = 0

    model.to(device)

    for epoch in range(1, num_epochs+1):
        model.train()
        train_loss_sum = 0.0
        train_count = 0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)

            optimizer.zero_grad()
            logits = model(batch_x)
            loss   = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()

            train_loss_sum += loss.item() * batch_x.size(0)
            train_count += batch_x.size(0)

        train_loss = train_loss_sum / train_count

        val_metrics = compute_classification_metrics(model, val_loader, device, num_classes)
        val_precision = val_metrics["precision_macro"]
        val_recall    = val_metrics["recall_macro"]
        val_f1        = val_metrics["f1_macro"]
        val_auc       = val_metrics["auc_macro"]

        print(f"Epoch {epoch}/{num_epochs} "
              f"Train Loss={train_loss:.4f}, "
              f"Val Precision={val_precision:.4f}, "
              f"Val Recall={val_recall:.4f}, "
              f"Val F1={val_f1:.4f}, "
              f"Val AUC={val_auc:.4f}")

        if scheduler is not None:
            if isinstance(scheduler, ReduceLROnPlateau):
                scheduler.step(train_loss)
            else:
                scheduler.step()

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_model_state = model.state_dict()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print("Early stopping triggered (macro-F1 did not improve).")
                break

    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    return model, best_val_f1

def main():
    from modules.modelClass import DirectionClassifierNet
    from modules.datasetClass import DirectionDataset
    import json

    set_seed(SEED)

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"CSV file '{CSV_FILE}' not found.")
    X, directions_str = load_classification_data(CSV_FILE)  
    print("Data loaded. X shape:", X.shape, " directions length:", len(directions_str))

    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    y_int = label_encoder.fit_transform(directions_str)
    num_classes = len(label_encoder.classes_)
    print("Classes found:", label_encoder.classes_)

    classes_list = label_encoder.classes_.tolist()
    with open(SAVE_CLASSES_JSON, "w") as f:
        json.dump(classes_list, f)
    print(f"Class list saved to '{SAVE_CLASSES_JSON}'")

    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(X, y_int, test_size=TEST_SIZE, random_state=SEED)
    print(f"Dataset: total={len(X)}, train={len(X_train)}, val={len(X_val)}, num_classes={num_classes}")

    # 5) Make Datasets & Loaders
    train_dataset = DirectionDataset(X_train, y_train)
    val_dataset   = DirectionDataset(X_val,   y_val)

    train_loader  = data.DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader    = data.DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False)

    model = DirectionClassifierNet(
        input_dim=3,
        hidden_dim=HIDDEN_DIM,
        output_dim=num_classes,
        num_hidden_layers=NUM_HIDDEN_LAYERS
    )

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2, verbose=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model, best_val_f1 = train_model_classification(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=nn.CrossEntropyLoss(),
        optimizer=optimizer,
        scheduler=scheduler,
        num_epochs=NUM_EPOCHS,
        patience=PATIENCE,
        device=device,
        num_classes=num_classes
    )

    print(f"\nBest macro-F1 on validation = {best_val_f1:.4f}")

    torch.save(model.state_dict(), SAVE_MODEL_PATH)
    print(f"Model saved to '{SAVE_MODEL_PATH}'")

    final_metrics = compute_classification_metrics(model, val_loader, device, num_classes)
    print("\nFinal Validation Metrics (Macro):")
    print(f"  Precision: {final_metrics['precision_macro']:.4f}")
    print(f"  Recall:    {final_metrics['recall_macro']:.4f}")
    print(f"  F1:        {final_metrics['f1_macro']:.4f}")
    print(f"  AUC:       {final_metrics['auc_macro']:.4f} (multi-class OVR)")
