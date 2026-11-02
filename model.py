import torch.nn as nn


class SteeringNet(nn.Module):
    """Petit réseau inspiré de PilotNet (NVIDIA) : image -> direction entre -1 et 1."""

    def __init__(self):
        super().__init__()
        # Les convolutions repèrent la route et ses bords
        self.features = nn.Sequential(
            nn.Conv2d(3, 24, kernel_size=5, stride=2, padding=2),  # 24 x 14 x 64
            nn.ReLU(),
            nn.Conv2d(24, 36, kernel_size=5, stride=2, padding=2),  # 36 x 7 x 32
            nn.ReLU(),
            nn.Conv2d(36, 48, kernel_size=3, stride=2, padding=1),  # 48 x 4 x 16
            nn.ReLU(),
            nn.Conv2d(48, 64, kernel_size=3, padding=1),  # 64 x 4 x 16
            nn.ReLU(),
        )
        # Les couches linéaires en déduisent un seul nombre
        self.regressor = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 4 * 16, 100),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(100, 50),
            nn.ReLU(),
            nn.Linear(50, 1),
            nn.Tanh(),  # Garde la sortie entre -1 et 1
        )

    def forward(self, x):
        return self.regressor(self.features(x)).squeeze(1)
