import torch
import torch.nn as nn
import numpy as np
from torch.autograd import Variable
from torch.nn.utils.rnn import pack_padded_sequence as pack
from torch.nn.utils.rnn import pad_packed_sequence as unpack
from Tree import *


class EncoderSDP(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers=1, dropout=0.1):
        super(EncoderSDP, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
    def forward(self, inputs, predicates, heads, lengths=None, hidden=None):
        batch_size, max_length, input_dim = inputs.size()
        outputs = []
        for b, head in enumerate(heads):
            root, tree = creatGRUTree(head)  # head: a sentence's heads; sentence base
            sentence_sub_paths = find_sentence_sub_paths(tree, predicates[b])
            output = []
            for sub_path_pair in sentence_sub_paths:
                left_path, right_path = sub_path_pair[0], sub_path_pair[1]
                left_path, right_path = Variable(torch.LongTensor(left_path)), Variable(torch.LongTensor(right_path))
                if torch.cuda.is_available():
                    left_path, right_path = left_path.cuda(), right_path.cuda()
                left_path_inputs, right_path_inputs = inputs[b].index_select(0, left_path), inputs[b].index_select(0, right_path)
                left_path_output, _ = torch.max(left_path_inputs, dim=0)  # max pooling
                left_path_output = left_path_output.view(1, -1)
                right_path_output, _ = torch.max(right_path_inputs, dim=0)  # max pooling
                right_path_output = right_path_output.view(1, -1)
                output.append(torch.cat([left_path_output, right_path_output], dim=1))
            output.extend([Variable(torch.zeros(1, (2 * self.hidden_size)), requires_grad=False).cuda()] * (max_length - len(head)))
            assert len(output) == max_length
            output = torch.cat(output, dim=0)
            outputs.append(output)
        outputs = torch.stack(outputs, dim=0)
        return outputs
