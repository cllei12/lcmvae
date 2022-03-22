from models.frozen_transformers import ImageCaptionEncoder
from models.vae import VAE

import torch
import torch.nn as nn


class LCMVAE(nn.Module):
    def __init__(self, VAEP, device=None):
        super(LCMVAE, self).__init__()
        self.config = VAEP
        self.device = torch.device(
            'cuda' if torch.cuda.is_available() else 'cpu') if device is None else device
        self.im_cap_encoder = ImageCaptionEncoder(device=device)
        self.vae = VAE(VAEP, device=device)
        
        
    def forward(self, images, captions):
        with torch.no_grad():
            im_cap_embedding = self.im_cap_encoder.forward(images, captions)
        vae_outputs = self.vae(im_cap_embedding)
        return vae_outputs

    def loss(self, target_images, vae_outputs, beta):
        return self.vae.loss(target_images, vae_outputs, beta)

    def reconstruct(self, images, captions):
        with torch.no_grad():
            im_cap_embedding = self.im_cap_encoder.forward(images, captions)
        reconstruction = self.vae.reconstruct(im_cap_embedding)
        return reconstruction
    
