# An integration of the VGG19 pretrained first layers, incorporated into the downsampling step of the UNet architecture
# to allow a fast identification of features used to generate segmentation

# MODULES

import torch
import torch.nn as nn
from Vgg19 import Vgg19
# DD

# DD. VGG19
# vgg19 = models.vgg19(pretrained=True)
# interp. an instance of nn containing the architecture and weights used for VGG19 with the ImageNet training data
# vgg19 = torch.load("./vgg19-dcbb9e9d.pth")
vgg19 = Vgg19()
vgg19.load_state_dict(torch.load("./vgg19-dcbb9e9d.pth"))
for param in vgg19.features.parameters():
    param.require_grad = False



# The Unet architecture is based on three main subarchitectures:
# downsampling
# bottleneck
# upsampling

# The downsampling process is divided in 4 blocks. A block contains
# two convolutions and Maxpooling.
# The bottleneck results from a convolution
# The upsampling is also divided in 4 blocks, which undo what the convolutions
# did during downsampling. Each upsampling block receives a skip connection from their
# downsampling counterpart, then applies two Deconvolutions
# Output is produced by a final deconvolution with a specified number of channels


######################## MODULES ########################
from constants import *

######################## DD #############################

# DD. DOUBLE_CONVOLUTION (DOWNSAMPLING BLOCK ELEMENT)
# conv = DoubleConv()
# interp. aubarchitecture to one DOWNSAMPLING block, in charge of extracting features
class DoubleConv(nn.Module):
    def __init__(self,in_channels, out_channels, kernel_size=3, padding=1):
        super().__init__()
        self.conv_op = nn.Sequential(
            nn.Conv2d(in_channels,out_channels,kernel_size=kernel_size,padding=padding),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels,out_channels,kernel_size=kernel_size,padding=padding),
            nn.ReLU(inplace=True),
        )
    def forward(self,x):
        return self.conv_op(x)

# DD. DOWNSAMPLE_BLOCK
# donwsample = DownSample()
# interp. an DOWNSAMPLE block represented by a DOUBLE_CONVOLUTION and its MaxPooling operation
class DownSample(nn.Module):
    def __init__(self,in_channels,out_channels):
        super().__init__()
        self.conv = DoubleConv(in_channels=in_channels,out_channels=out_channels)
        self.pool = nn.MaxPool2d(kernel_size=2,stride=2)

    def forward(self,x):
        down = self.conv(x)
        p = self.pool(down)
        return down,p

# DD. DOWNSAMPLE_BLOCK_VGG19
# downsample = DownsampleVGG19()
# interp. a DOWNSAMPLE block represented by a pass across a subset of VGG19 feature extractor
class DownSampleVGG(nn.Module):
    def __init__(self,range_from_VGG, in_channels,out_channels, pool_kernel_size=2, pool_stride=2):
        super().__init__()
        low_bound,upper_bound = range_from_VGG
        self.conv = nn.Sequential(*list(vgg19.features.children())[low_bound:upper_bound])
        self.pool = nn.MaxPool2d(kernel_size=pool_kernel_size,stride=pool_stride)
    
    def forward(self,x):
        down = self.conv(x)
        p = self.pool(down)
        return down,p





# DD. UPSAMPLE_DECONVOLUTION_BLOCK (UPSAMPLING BLOCK)
# upsample = UpSample()
# interp. an UPSAMPLE block represented by:
# - a "deconvolution" (ConvTranspose2d)
# - a concatenation with a parallel version from the encoder
# - Double convolution
class UpSample(nn.Module):
    def __init__(self,in_channels_up,out_channels_up, reduce_channels_in_half=True, kernel_size = 2, stride=2, use_corrective_conv=False, in_channels_conv=None,out_channels_conv=None):
        super().__init__()
            
        if reduce_channels_in_half:
            self.up = nn.ConvTranspose2d(in_channels_up, in_channels_up//2,kernel_size=kernel_size,stride = stride)
        else:
            self.up = nn.ConvTranspose2d(in_channels_up, in_channels_up,kernel_size=kernel_size,stride = stride)
            
            
        # In some cases the dimensions of the upsampling and the convolution from concatenation don't match, requiring a corretive step that indicates which dimensions to use
        if not use_corrective_conv:
            self.in_channels_conv = in_channels_up
            self.out_channel_conv = out_channels_up
        else:
            self.in_channels_conv = in_channels_conv
            self.out_channel_conv = out_channels_conv
        self.conv = DoubleConv(in_channels=self.in_channels_conv,out_channels=self.out_channel_conv)

    def forward(self,x1,x2):
        x1 = self.up(x1)
        x = torch.cat([x1,x2],1)
        return self.conv(x)

# DD. UnetVgg()
# unetVgg = pytorch.nn.Module()
# interp. a complete architecture to represent a UNet model with
# - at least 4 DownSample()
# - at least 4 UpSample()
class UNetVgg19(nn.Module):
    def __init__(self,in_channels=3,num_classes=1):
        super().__init__()
        # enters 3, exits 64 - 0 to 3 (+1 to account for exclusion of last element)               image res 512 x 512
        self.downsample1 = DownSampleVGG((0,4),3,64)
        # enters 64, exits 128 - 5 to 8 (+1 to account for exclusion of last element)             image res 256 x 256
        self.downsample2 = DownSampleVGG((5,9),64,128)
        # enters 128, exits 256 - 10 to 17 (+1 to account for exclusion of last element)          image res 128 x 128
        self.downsample3 = DownSampleVGG((10,18),128,256)
        # enters 256, exits 512 - 19 to 26 (+1 to account for exclusion of last element)          image res 64 x 64
        self.downsample4 = DownSampleVGG((19,27),256,512)
        # enters 512, exits 512 - 28 to 35 (+1 to account for exclusion of last element)          image res 64 x 64
        # self.downsample5 = DownSampleVGG((28,36),512,512, pool_kernel_size=1, pool_stride=1) # we can keep the image dimensions at 32 with kernelsize 1 and stride 1

        # self.downsample1 = DownSampleVGG((0,4),3,64)
        # self.downsample2 = DownSampleVGG((5,9),64,128)
        # self.downsample3 = DownSampleVGG((10,16),128,256)
        # self.downsample4 = DownSampleVGG((17,23),256,512)
        
        self.bottle_neck = DoubleConv(512,1024)

        
        self.upsample1 = UpSample(1024,512) #
        # self.upsample2 = UpSample(512,512, reduce_channels_in_half=False, use_corrective_conv=True, in_channels_conv=1024,out_channels_conv=512)
        self.upsample2 = UpSample(512,256)
        self.upsample3 = UpSample(256,128)
        self.upsample4 = UpSample(128,64)
        self.out = nn.Conv2d(in_channels=64, out_channels=num_classes,kernel_size=1)

    def forward(self,x):
        down1, p1 = self.downsample1(x)
        down2, p2 = self.downsample2(p1)
        down3, p3 = self.downsample3(p2)
        down4, p4 = self.downsample4(p3)
        # down5, p5 = self.downsample5(p4)

        b = self.bottle_neck(p4)

        up1 = self.upsample1(b,down4)
        up2 = self.upsample2(up1,down3)
        up3 = self.upsample3(up2,down2)
        up4 = self.upsample4(up3,down1)

        out = self.out(up4)
        return out
######################## CODE ###########################


# if __name__ == "__main__":
#     model = UNet(10,3)