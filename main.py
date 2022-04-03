from models.basic_models.linear import Encoder, Decoder
from models.lcmvae import LCMVAE
from models.heads import ConvDecoder512
from models.standalone_vae import StandaloneVAE
from models.params import LCMVAE_PARAMS as LCMVAEP
from models.params import CONV_DECODER_512_PARAMS as CD512P
from models.params import STANDALONE_VAE_PARAMS as SVAEP
from train import Trainer
from test import Tester
from params import PRETRAIN_PARAMS as PTP
from params import PRETEST_PARAMS as PTEP
from params import TRAIN_PARAMS as TP
from params import TEST_PARAMS as TEP
from utils import load_checkpoint, denormalize_torch_to_cv2
from params import PRETRAIN_DATASET_PARAMS

import cv2
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import numpy as np

from PIL import Image
import numpy as np

from torch.utils.data import DataLoader
from dataset import MyCocoCaption, MyCocoCaptionDetection

from datetime import date
    
def main():
    today = date.today()
    experiment_name = "sample_run" + today.strftime("-%Y-%m-%d") 
    # experiment_name = "trained_experiment_name"
    pretrain = True
    pretest = False
    train = True
    test = False


    device = torch.device(
        'cuda' if torch.cuda.is_available() else 'cpu')
    
    # # Construct Dataset
    # coco_val2017 = MyCocoCaption(root = PRETRAIN_DATASET_PARAMS.image_dir,
    #                             annFile = PRETRAIN_DATASET_PARAMS.ann_file,
    #                             from_pretrained = PRETRAIN_DATASET_PARAMS.from_pretrained)

    # detection dataset: outputs: img, (caption, mask)
    # cats = {1: 'person', 2: 'bicycle', 3: 'car',4: 'motorcycle', 5: 'airplane', 6: 'bus', 7: 'train', 8: 'truck', 9: 'boat'}
    coco_val2017 = MyCocoCaptionDetection(root=PRETRAIN_DATASET_PARAMS.image_dir,
                                  annFile=PRETRAIN_DATASET_PARAMS.ann_file,
                                  detAnnFile=PRETRAIN_DATASET_PARAMS.det_ann_file,
                                  superclasses=["person", "vehicle"],
                                  from_pretrained=PRETRAIN_DATASET_PARAMS.from_pretrained)

    # image mean and std for reconstruction
    image_mean = torch.tensor(coco_val2017.feature_extractor.image_mean)
    image_std = torch.tensor(coco_val2017.feature_extractor.image_std)

    # Check the info of dataset, you can ignore this part
    print('-'*40)
    coco_val2017.coco.info()
    print('-'*40)
    print(f'The number of samples: {len(coco_val2017)}')
    first_img, (first_cap, first_segment) = coco_val2017[0]
    print(f'Image shape: {first_img.size()}')
    
    # Build Dataloader for pretrain
    data_loader = DataLoader(dataset = coco_val2017, 
                            #  batch_size=PRETRAIN_DATASET_PARAMS.batch_size, 
                             batch_size=2,
                             shuffle=PRETRAIN_DATASET_PARAMS.shuffle, 
                             num_workers=PRETRAIN_DATASET_PARAMS.num_workers)

    # # Check: print info for each batch
    # i = 0
    # for imgs, (caps, segment) in data_loader:
    #     print(f'batch_{i}')
    #     print(f"Image batch shape: {imgs.size()}")
    #     print(f"Segmentation batch shape: {segment.size()}")
    #     print(f"Caption batch shape: {len(caps)}")
    #     i += 1
    # exit()
    
    lcmvae = LCMVAE(LCMVAEP, device=device)
    # svae = StandaloneVAE(SVAEP, device=device)
    if pretrain:
        pretrainer = Trainer(lcmvae, PTP, experiment_name=experiment_name+"_pretrain")
        pretrainer.run(data=data_loader)

    if pretest:
        # lcmvae.im_cap_encoder.vit.model.config.mask_ratio = 0
        encoder = Encoder(LCMVAEP.vae_params.encoder_params)
        decoder = Decoder(LCMVAEP.vae_params.decoder_params)
        load_checkpoint(encoder, name=experiment_name+"_pretrain")
        load_checkpoint(decoder, name=experiment_name+"_pretrain")
        lcmvae.vae.encoder = encoder
        lcmvae.vae.decoder = decoder
        # svae.encoder = encoder
        # svae.decoder = encoder

        tester = Tester(
            lcmvae, PTEP, experiment_name=experiment_name+"_pretest")
        tester.run(data=data_loader)

        for i in range(10):
            im, (cap, _) = coco_val2017[i]
            target = denormalize_torch_to_cv2(im, image_mean, image_std)
            reconstruction, mask = lcmvae.run(im[None], [cap])
            # reconstruction = svae.reconstruct(im[None])["reconstruction"]
            prediction = denormalize_torch_to_cv2(
                reconstruction, image_mean, image_std)
            result = np.concatenate((target, prediction), axis=1)
            cv2.imwrite(f"output/{experiment_name}_{i}.jpg", result)

    if train:
        lcmvae.im_cap_encoder.vit.model.config.mask_ratio = 0
        encoder = Encoder(LCMVAEP.vae_params.encoder_params)
        decoder = ConvDecoder512(CD512P)
        load_checkpoint(encoder, name=experiment_name+"_pretrain")
        lcmvae.vae.encoder = encoder
        lcmvae.vae.decoder = decoder
        criterion = nn.CrossEntropyLoss(reduction="sum")
        trainer = Trainer(lcmvae, TP, experiment_name=experiment_name+"_train", downstream_criterion=criterion)
        trainer.run(data=data_loader)

    if test:
        lcmvae.im_cap_encoder.vit.model.config.mask_ratio = 0
        encoder = Encoder(LCMVAEP.vae_params.encoder_params)
        decoder = ConvDecoder512(CD512P)
        load_checkpoint(encoder, name=experiment_name+"_train")
        load_checkpoint(decoder, name=experiment_name+"_train")
        lcmvae.vae.encoder = encoder
        lcmvae.vae.decoder = decoder
        criterion = nn.CrossEntropyLoss(reduction="sum")

        tester = Tester(
            lcmvae, PTEP, experiment_name=experiment_name+"_test", downstream_criterion=criterion)
        tester.run(data=data_loader)

        im, (cap, seg) = coco_val2017[0]
        reconstruction, mask = lcmvae.run(im[None], [cap])
        prediction = torch.argmax(reconstruction, dim=0)
        print(mask)
        print(prediction.shape)
        print(f"Actual classes: {torch.unique(seg)}")
        print(f"Predicted classes: {torch.unique(prediction)}")
        plt.figure(figsize=(12, 5))
        plt.subplot(121)
        plt.imshow(seg.squeeze(), vmin=0, vmax=9)
        plt.subplot(122)
        plt.imshow(prediction.squeeze(), vmin=0, vmax=9)
        plt.savefig(f"output/{experiment_name}_segmentation.jpg")

        

    

if __name__=="__main__":
    main()
