import torch
import torch.nn as nn


# TODO: convert hidden channels into params
class ConvDecoder512(nn.Module):
  """
  Convoluted Decoder for LCMVAE. (Temporary)
  in_dim:  
  """
  def __init__(self, embed_dim):
    super().__init__()
    self.map = nn.Linear(embed_dim, 512, bias=True)   # for initial Linear layer
    self.net = nn.Sequential(
      nn.BatchNorm2d(512),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=512, out_channels=256, kernel_size=3,
                stride=1, padding=0, bias=True),
      nn.BatchNorm2d(256),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=256, out_channels=128, kernel_size=3,
                stride=2, padding=0, bias=True),
      nn.BatchNorm2d(128),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=128, out_channels=64, kernel_size=4,
                stride=2, padding=0, bias=True),
      nn.BatchNorm2d(64),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=64, out_channels=32, kernel_size=8,
                stride=3, padding=0, bias=True),
      nn.BatchNorm2d(32), 
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=32, out_channels=3, kernel_size=16,
                stride=4, padding=0, bias=True)
    )
  
  def forward(self, x):
    return self.net(self.map(x).reshape(-1, 512, 1, 1))



# TODO: TESTING NEEDED
class DirectDeconvDecoder(nn.Module):
  """
  Convoluted Decoder for LCMVAE.
  in_dim:  
  """
  def __init__(self, embed_dim):
    super().__init__()
    self.map = nn.Linear(embed_dim, 1536, bias=True)   # for initial Linear layer
    self.net = nn.Sequential(
      nn.BatchNorm2d(1536),
      nn.LeakyReLU(),      
      nn.ConvTranspose2d(in_channels=1536, out_channels=768, kernel_size=3,
                stride=1, padding=0, bias=True),
      nn.BatchNorm2d(256),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=768, out_channels=256, kernel_size=3,
                stride=1, padding=0, bias=True),
      nn.BatchNorm2d(256),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=256, out_channels=84, kernel_size=3,
                stride=2, padding=0, bias=True),
      nn.BatchNorm2d(64),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=84, out_channels=42, kernel_size=4,
                stride=1, padding=0, bias=True),
      nn.BatchNorm2d(32),
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=42, out_channels=21, kernel_size=4,
                stride=2, padding=0, bias=True),
      nn.BatchNorm2d(16), 
      nn.LeakyReLU(),
      nn.ConvTranspose2d(in_channels=21, out_channels=3, kernel_size=6,
                stride=2, padding=0, bias=True)
    )
  
  def forward(self, x):
    return self.net(self.map(x).reshape(-1, 1536, 1, 1))
