import torch
import torch.nn as nn

class EvoNorm(nn.Module):
    def __init__(self, input, non_linear = True, version = 'S0', momentum = 0.9, eps = 1e-5, training = True):
        super(EvoNorm, self).__init__()
        self.non_linear = non_linear
        self.version = version
        self.training = training
        self.momentum = momentum
        self.eps = eps
        if self.version not in ['B0', 'S0']:
            raise ValueError("Invalid EvoNorm version")
        self.insize = input
        self.gamma = nn.Parameter(torch.ones(1, self.insize, 1, 1))
        self.beta = nn.Parameter(torch.zeros(1, self.insize, 1, 1))
        if self.non_linear:
            self.v = nn.Parameter(torch.ones(1,self.insize,1,1))
        self.register_buffer('running_var', torch.ones(1, self.insize, 1, 1))

        self.reset_parameters()

    def reset_parameters(self):
        self.running_var.fill_(1)
    
    def forward(self, x):
        if x.dim() != 4:
            raise ValueError('expected 4D input (got {}D input)'
                             .format(x.dim()))
        if self.version == 'S0':
            if self.non_linear:
                num = x * torch.sigmoid(self.v * x)
                return num / group_std(x, eps = self.eps) * self.gamma + self.beta
            else:
                return x * self.gamma + self.beta
        if self.version == 'B0':
            if self.training:
                var = torch.var(x, dim = (0, 2, 3), unbiased = False, keepdim = True).reshape(1, x.size(1), 1, 1)
                with torch.no_grad():
                   self.running_var.copy_(self.momentum * self.running_var + (1 - self.momentum) * var)
            else:
                var = self.running_var

            if self.non_linear:
                den = torch.max((var+self.eps).sqrt(), self.v * x + instance_std(x, eps = self.eps))
                return x / den * self.gamma + self.beta
            else:
                return x * self.gamma + self.beta