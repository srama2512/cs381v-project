import torch
import pdb
import torch.nn as nn
import torch.nn.functional as F
import time
from graphviz import Digraph

def ixvr(input_layer, bias_val=0):
    nn.init.xavier_normal(input_layer.weight);
    nn.init.constant(input_layer.bias, bias_val);
    return input_layer

def inrml(input_layer, mean=0, std=0.05):
    nn.init.normal(input_layer.weight, mean, std);
    nn.init.constant(input_layer.bias, 0.1);
    return input_layer

class ModelJoint(nn.Module):
    
    def __init__(self):
        super(ModelJoint, self).__init__()
        self.base_conv = nn.Sequential(
                          inrml(nn.Conv2d(3, 20, 7, stride=1, padding=3)), # 3x101x101 -> 20x101x101
                          nn.ReLU(inplace=True), 
                          nn.BatchNorm2d(20),
                          nn.MaxPool2d(2, stride=2), # 20x50x50
                          inrml(nn.Conv2d(20, 40, 5, stride=1, padding=2)), # 40x50x50
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(40),
                          nn.MaxPool2d(2, stride=2), # 40x25x25
                          inrml(nn.Conv2d(40, 80, 4, stride=1, padding=1)), # 80x24x24
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(80),
                          nn.MaxPool2d(2, stride=2), # 80x12x12
                          inrml(nn.Conv2d(80, 160, 4, stride=2, padding=1)), # 160x6x6
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(160),
                          nn.MaxPool2d(2, stride=2)) # 160x3x3

        self.base_fc = nn.Sequential(
                          inrml(nn.Linear(1440, 500)), 
                          nn.ReLU(inplace=True),
                          #nn.Dropout(p=0.5),
                          inrml(nn.Linear(500, 500)),
                          nn.ReLU(inplace=True))
                          #nn.Dropout(p=0.5))
        
        self.pose_regressor = inrml(nn.Linear(1000, 5))
        self.matcher = inrml(nn.Linear(1000, 1))

    def forward(self, inputs):
        #t1 = time.clock()
        p = self.forward_pose(inputs['pose'][0], inputs['pose'][1])
        m = self.forward_match(inputs['match'][0], inputs['match'][1])
        #print('Forward time: %.5f seconds'%(time.clock()-t1))
        return p, m

    def forward_pose(self, imgs_left, imgs_right):
        xl = self.base_conv(imgs_left)
        xr = self.base_conv(imgs_right)
        xl = xl.view(-1, 1440)
        xr = xr.view(-1, 1440)
        xl = self.base_fc(xl)
        xr = self.base_fc(xr)
        xc = torch.cat((xl, xr), dim=1)
        xc = self.pose_regressor(xc)

        return xc

    def forward_match(self, imgs_left, imgs_right):
        xl = self.base_conv(imgs_left)
        xr = self.base_conv(imgs_right)
        xl = xl.view(-1, 1440)
        xr = xr.view(-1, 1440)
        xl = self.base_fc(xl)
        xr = self.base_fc(xr)
        xc = torch.cat((xl, xr), dim=1)
        xc = self.matcher(xc)

        return xc

    def forward_feature(self, imgs):
        x = self.base_conv(imgs)
        x = x.view(-1, 1440)
        x = self.base_fc(x)

        return x
        
class ModelPose(nn.Module):
    
    def __init__(self):
        super(ModelPose, self).__init__()
        self.base_conv = nn.Sequential(
                          inrml(nn.Conv2d(3, 20, 7, stride=1, padding=3)), # 3x101x101 -> 20x101x101
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(20),
                          nn.MaxPool2d(2, stride=2), # 20x50x50
                          inrml(nn.Conv2d(20, 40, 5, stride=1, padding=2)), # 40x50x50
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(40),
                          nn.MaxPool2d(2, stride=2), # 40x25x25
                          inrml(nn.Conv2d(40, 80, 4, stride=1, padding=1)), # 80x24x24
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(80),
                          nn.MaxPool2d(2, stride=2), # 80x12x12
                          inrml(nn.Conv2d(80, 160, 4, stride=2, padding=1)), # 160x6x6
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(160),
                          nn.MaxPool2d(2, stride=2)) # 160x3x3

        self.base_fc = nn.Sequential(
                          inrml(nn.Linear(1440, 500)), 
                          nn.ReLU(inplace=True),
                          #nn.Dropout(p=0.5),
                          inrml(nn.Linear(500, 500)),
                          nn.ReLU(inplace=True))
                          #nn.Dropout(p=0.5))
        
        self.pose_regressor = nn.Sequential(
                                #inrml(nn.Linear(1000, 200)),
                                #nn.ReLU(inplace=True),
                                inrml(nn.Linear(1000, 5)))

    def forward(self, imgs_left, imgs_right):
        xl = self.base_conv(imgs_left)
        xr = self.base_conv(imgs_right)
        xl = xl.view(-1, 1440)
        xr = xr.view(-1, 1440)
        xl = self.base_fc(xl)
        xr = self.base_fc(xr)
        xc = torch.cat((xl, xr), dim=1)
        xc = self.pose_regressor(xc)

        return xc
    
    def forward_pose(self, imgs_left, imgs_right):
        xl = self.base_conv(imgs_left)
        xr = self.base_conv(imgs_right)
        xl = xl.view(-1, 1440)
        xr = xr.view(-1, 1440)
        xl = self.base_fc(xl)
        xr = self.base_fc(xr)
        xc = torch.cat((xl, xr), dim=1)
        xc = self.pose_regressor(xc)

        return xc

    def forward_feature(self, imgs):
        x = self.base_conv(imgs)
        x = x.view(-1, 1440)
        x = self.base_fc(x)

        return x
       
class ModelMatch(nn.Module):
    
    def __init__(self):
        super(ModelMatch, self).__init__()
        self.base_conv = nn.Sequential(
                          inrml(nn.Conv2d(3, 20, 7, stride=1, padding=3)), # 3x101x101 -> 20x101x101
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(20),
                          nn.MaxPool2d(2, stride=2), # 20x50x50
                          inrml(nn.Conv2d(20, 40, 5, stride=1, padding=2)), # 40x50x50
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(40),
                          nn.MaxPool2d(2, stride=2), # 40x25x25
                          inrml(nn.Conv2d(40, 80, 4, stride=1, padding=1)), # 80x24x24
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(80),
                          nn.MaxPool2d(2, stride=2), # 80x12x12
                          inrml(nn.Conv2d(80, 160, 4, stride=2, padding=1)), # 160x6x6
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(160),
                          nn.MaxPool2d(2, stride=2)) # 160x3x3

        self.base_fc = nn.Sequential(
                          inrml(nn.Linear(1440, 500)), 
                          nn.ReLU(inplace=True),
                          #nn.Dropout(p=0.5),
                          inrml(nn.Linear(500, 500)),
                          nn.ReLU(inplace=True))
                          #nn.Dropout(p=0.5))
        
        self.matcher = nn.Sequential(
                            inrml(nn.Linear(1000, 1))
                            )

    def forward(self, imgs_left, imgs_right):
        xl = self.base_conv(imgs_left)
        xr = self.base_conv(imgs_right)
        xl = xl.view(-1, 1440)
        xr = xr.view(-1, 1440)
        xl = self.base_fc(xl)
        xr = self.base_fc(xr)
        xc = torch.cat((xl, xr), dim=1)
        xc = self.matcher(xc)

        return xc

    def forward_match(self, imgs_left, imgs_right):
        xl = self.base_conv(imgs_left)
        xr = self.base_conv(imgs_right)
        xl = xl.view(-1, 1440)
        xr = xr.view(-1, 1440)
        xl = self.base_fc(xl)
        xr = self.base_fc(xr)
        xc = torch.cat((xl, xr), dim=1)
        xc = self.matcher(xc)

        return xc

    def forward_feature(self, imgs):
        x = self.base_conv(imgs)
        x = x.view(-1, 1440)
        x = self.base_fc(x)

        return x

class ModelSurfaceNormal(nn.Module):
    def __init__(self):
        super(ModelSurfaceNormal, self).__init__()
        self.base_conv = nn.Sequential(
                          inrml(nn.Conv2d(3, 20, 7, stride=1, padding=3)), # 3x101x101 -> 20x101x101
                          nn.ReLU(inplace=True), 
                          nn.BatchNorm2d(20),
                          nn.MaxPool2d(2, stride=2), # 20x50x50
                          inrml(nn.Conv2d(20, 40, 5, stride=1, padding=2)), # 40x50x50
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(40),
                          nn.MaxPool2d(2, stride=2), # 40x25x25
                          inrml(nn.Conv2d(40, 80, 4, stride=1, padding=1)), # 80x24x24
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(80),
                          nn.MaxPool2d(2, stride=2), # 80x12x12
                          inrml(nn.Conv2d(80, 160, 4, stride=2, padding=1)), # 160x6x6
                          nn.ReLU(inplace=True),
                          nn.BatchNorm2d(160),
                          nn.MaxPool2d(2, stride=2)) # 160x3x3

        self.base_fc = nn.Sequential(
                          inrml(nn.Conv2d(160, 500, 3, stride=1, padding=0)), 
                          nn.ReLU(inplace=True),
                          inrml(nn.Conv2d(500, 500, 1, stride=1, padding=0)),
                          nn.ReLU(inplace=True))
                        
        # Classify into 20 classes
        self.classifier = nn.Sequential(
                          inrml(nn.Conv2d(500, 20, 1, stride=1, padding=0)))
    
    def load_weights(self, state_dict):
        """
        Loads directly from a joint/pose/match network's stored checkpoint
        """
        own_state = self.state_dict()
        # Copy the convloutional layers
        for name, param in state_dict.iteritems():
            if 'base_conv' in name:
                own_state[name].copy_(param)
        # Convert the FC layers to convolutional layers
        own_state['base_fc.0.weight'].copy_(state_dict['base_fc.0.weight'].view(500, 160, 3, 3))
        own_state['base_fc.0.bias'].copy_(state_dict['base_fc.0.bias'])
        own_state['base_fc.2.weight'].copy_(state_dict['base_fc.2.weight'].view(500, 500, 1, 1))
        own_state['base_fc.2.bias'].copy_(state_dict['base_fc.2.bias'])
        
        # Freeze the weights for the initial Conv and FC layers
        for i in range(len(self.base_conv)):
            if hasattr(self.base_conv[i], 'weight'):
                self.base_conv[i].weight.requires_grad = False
            if hasattr(self.base_conv[i], 'bias'):
                self.base_conv[i].bias.requires_grad = False
        
        for i in range(len(self.base_fc)):
            if hasattr(self.base_fc[i], 'weight'):
                self.base_fc[i].weight.requires_grad = False
            if hasattr(self.base_fc[i], 'bias'):
                self.base_fc[i].bias.requires_grad = False

    def forward(self, x):
        x = self.base_conv(x)
        x = self.base_fc(x)
        x = self.classifier(x)
        return x

