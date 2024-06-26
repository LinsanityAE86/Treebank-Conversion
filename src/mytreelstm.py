# import torch
# import torch.nn as nn
# from torch.nn.utils.rnn import pad_sequence
#
# from mytree import *
# import numpy as np
#
#
# class BiTreeLSTM(nn.Module):
#     def __init__(self, input_dim, hidden_dim, dropout_ratio):
#         super(BiTreeLSTM, self).__init__()
#         self.dropout_ratio = dropout_ratio
#         self._input_dim = input_dim
#         self._hidden_dim = hidden_dim
#         self.dt_treelstm = DTTreeLSTM(input_dim, hidden_dim, dropout_ratio)
#         self.td_treelstm = TDTreeLSTM(input_dim, hidden_dim, dropout_ratio)
#
#     def forward(self, inputs, heads):
#         max_length, batch_size, dim = inputs.size()
#         assert dim == self._input_dim
#         trees = []
#         # heads = heads.tolist()
#         indexes = np.zeros((max_length, batch_size), dtype=np.int32)
#         for b, head in enumerate(heads):
#             root, tree = creatTree(head)
#             root.traverse()
#             for step, index in enumerate(root.order):
#                 indexes[step, b] = index
#             trees.append(tree)
#
#         dt_cells, dt_hiddens = self.dt_treelstm(inputs, indexes, trees)
#         td_cells, td_hiddens = self.td_treelstm(inputs, indexes, trees)
#
#         # 假设dt_lengths는dt的长度,td_lengths是td的长度
#
#         # dt_cells = pad_sequence(dt_cells, batch_first=True, padding_value=0)
#         # td_cells = pad_sequence(td_cells, batch_first=True, padding_value=0)
#         #
#         # dt_hiddens = pad_sequence(dt_hiddens, batch_first=True, padding_value=0)
#         # td_hiddens = pad_sequence(td_hiddens, batch_first=True, padding_value=0)
#
#         return torch.cat((dt_cells, td_cells), dim=2), torch.cat((dt_hiddens, td_hiddens), dim=2)
#
#         return torch.cat((dt_cells, td_cells), dim=2), torch.cat((dt_hiddens, td_hiddens), dim=2)
#
#
# # module for childsumtreelstm
# class DTTreeLSTM(nn.Module):
#     def __init__(self, input_dim, hidden_dim, dropout_ratio):
#         super(DTTreeLSTM, self).__init__()
#         self._input_dim = input_dim
#         self._hidden_dim = hidden_dim
#         self.ioux = nn.Linear(self._input_dim, 3 * self._hidden_dim)
#         self.iouh = nn.Linear(self._hidden_dim, 3 * self._hidden_dim)
#         self.fx = nn.Linear(self._input_dim, self._hidden_dim)
#         self.fh = nn.Linear(self._hidden_dim, self._hidden_dim)
#
#         self.dropout = nn.Dropout(dropout_ratio)
#
#     def node_forward(self, xs, sum_child_cs, sum_child_hs):
#
#         iou = self.ioux(xs) + self.iouh(sum_child_hs)
#         i, o, u = torch.split(iou, iou.size(1) // 3, dim=1)
#         i, o, u = torch.sigmoid(i), torch.sigmoid(o), torch.tanh(u)
#
#         f = torch.sigmoid(
#             self.fh(sum_child_hs) + self.fx(xs)
#         )
#         fc = torch.mul(f, sum_child_cs)
#
#         c = torch.mul(i, u) + fc  # torch.sum(fc, dim=0, keepdim=True)
#         h = torch.mul(o, torch.tanh(c))
#         return c, h
#
#
#     def forward(self, inputs, indexes, trees):
#         max_length, batch_size, input_dim = inputs.size()
#
#         steps_inputs = inputs[indexes, torch.arange(batch_size)]
#         dt_state_c, dt_state_h = [], []
#         for b in range(batch_size):
#             dt_state_c.append({})
#             dt_state_h.append({})
#
#         for step in range(max_length):
#             step_inputs = steps_inputs[step]
#             sum_child_cs, sum_child_hs = [], []
#             # step_inputs, sum_child_cs, sum_child_hs = [], [], []
#             for b, tree in enumerate(trees):
#                 index = indexes[step, b]
#
#                 print("child index:", [child.index for child in tree[index].children])
#                 print("dt_state_c keys:", list(dt_state_c[b].keys()))
#                 if tree[index].children_num == 0:
#                     sum_child_c = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
#                     sum_child_h = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
#                 else:
#                     child_c_list = [dt_state_c[b][child.index] for child in tree[index].children]
#                     child_c = torch.stack(child_c_list, 0)
#                     sum_child_c = torch.sum(child_c, dim=0)
#
#                     child_h_list = [dt_state_h[b][child.index] for child in tree[index].children]
#                     child_h = torch.stack(child_h_list, 0)
#                     sum_child_h = torch.sum(child_h, dim=0)
#
#                 sum_child_cs.append(sum_child_c)
#                 sum_child_hs.append(sum_child_h)
#             sum_child_cs = torch.stack(sum_child_cs, 0)
#             sum_child_hs = torch.stack(sum_child_hs, 0)
#             # when training, drop; when eval, not drop
#             sum_child_hs = self.dropout(sum_child_hs)
#
#             step_results = self.node_forward(step_inputs, sum_child_cs, sum_child_hs)
#             for b in range(batch_size):
#                 index = indexes[step, b]
#                 dt_state_c[b][index], dt_state_h[b][index] = step_results[0][b], step_results[1][b]
#
#         hiddens, cells = [], []
#         for b in range(batch_size-1):
#             one_sent_cells = [dt_state_c[b][idx] for idx in range(0, max_length)]
#             one_sent_hiddens = [dt_state_h[b][idx] for idx in range(0, max_length)]
#
#             cells.append(torch.stack(one_sent_cells, 0))
#             hiddens.append(torch.stack(one_sent_hiddens, 0))
#         return torch.stack(cells, dim=0).transpose(0, 1), torch.stack(hiddens, dim=0).transpose(0, 1)
#
#
# class TDTreeLSTM(nn.Module):
#     def __init__(self, input_dim, hidden_dim, dropout_ratio):
#         super(TDTreeLSTM, self).__init__()
#         self._input_dim = input_dim
#         self._hidden_dim = hidden_dim
#         self.ioux = nn.Linear(self._input_dim, 3 * self._hidden_dim)
#         self.iouh = nn.Linear(self._hidden_dim, 3 * self._hidden_dim)
#         self.fx = nn.Linear(self._input_dim, self._hidden_dim)
#         self.fh = nn.Linear(self._hidden_dim, self._hidden_dim)
#
#         self.dropout = nn.Dropout(dropout_ratio)
#
#     def node_forward(self, xs, sum_child_cs, sum_child_hs):
#
#         iou = self.ioux(xs) + self.iouh(sum_child_hs)
#         i, o, u = torch.split(iou, iou.size(1) // 3, dim=1)
#         i, o, u = torch.sigmoid(i), torch.sigmoid(o), torch.tanh(u)
#
#         f = torch.sigmoid(
#             self.fh(sum_child_hs) + self.fx(xs)
#         )
#         fc = torch.mul(f, sum_child_cs)
#
#         c = torch.mul(i, u) + fc  # torch.sum(fc, dim=0, keepdim=True)
#         h = torch.mul(o, torch.tanh(c))
#         return c, h
#
#     def forward(self, inputs, indexes, trees):
#         # print("#### ", self.dropout.training)
#         max_length, batch_size, input_dim = inputs.size()
#         steps_inputs = inputs[indexes, torch.arange(batch_size)]
#         dt_state_c, dt_state_h = [], []
#         for b in range(batch_size):
#             dt_state_c.append({})
#             dt_state_h.append({})
#
#         for step in reversed(range(max_length)):
#             # step_inputs, parent_cs, parent_hs = [], [], []
#             parent_cs, parent_hs = [], []
#             step_inputs = steps_inputs[step]
#             for b, tree in enumerate(trees):
#                 index = indexes[step, b]
#                 if tree[index].parent is None:
#                     parent_c = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
#                     parent_h = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
#                 else:
#                     parent_c = dt_state_c[b][tree[index].parent.index]
#                     parent_h = dt_state_h[b][tree[index].parent.index]
#                 parent_cs.append(parent_c)
#                 parent_hs.append(parent_h)
#
#             parent_cs = torch.stack(parent_cs, 0)
#             parent_hs = torch.stack(parent_hs, 0)
#
#             parent_hs = self.dropout(parent_hs)
#             step_results = self.node_forward(step_inputs, parent_cs, parent_hs)
#
#             for b in range(batch_size):
#                 index = indexes[step, b]
#                 dt_state_c[b][index], dt_state_h[b][index] = step_results[0][b], step_results[1][b]
#
#         hiddens, cells = [], []
#         for b in range(batch_size):
#             one_sent_cells = [dt_state_c[b][idx] for idx in range(0, max_length)]
#             one_sent_hiddens = [dt_state_h[b][idx] for idx in range(0, max_length)]
#
#             cells.append(torch.stack(one_sent_cells, 0))
#             hiddens.append(torch.stack(one_sent_hiddens, 0))
#         return torch.stack(cells, dim=0).transpose(0, 1), torch.stack(hiddens, dim=0).transpose(0, 1)
#
#
# if __name__ == '__main__':
#
#     treelstm = DTTreeLSTM(10, 20, dropout_ratio=0.5)
#
#     print("test node forward: ")
#     xs = torch.randn((5, 10))
#     sum_child_c = torch.randn((5, 20))
#     sum_child_h = torch.randn((5, 20))
#     rep = treelstm.node_forward(xs, sum_child_c, sum_child_h)
#     print(rep[0].size())
#     print(rep[1].size())
#     print("test node forward OK")
#
#     print("test forward: ")
#     inputs = torch.randn((6, 2, 10))
#     max_length, batch_size, dim = inputs.size()
#     heads = [[-1, 2, 0, 2, 2, 1], [-1, 2, 0, 2, 2, 1]]
#     trees = []
#     indexes = np.zeros((max_length, batch_size), dtype=np.int32)
#     for b, head in enumerate(heads):
#         root, tree = creatTree(head)
#         root.traverse()
#         for step, index in enumerate(root.order):
#             indexes[step, b] = index
#         trees.append(tree)
#     rep = treelstm.forward(inputs, indexes, trees)
#     print(rep[0].size())
#     print(rep[1].size())
#
#     print("test forward OK")
#
#     print("test TDTreeLSTM：")
#     treelstm = TDTreeLSTM(10, 20, dropout_ratio=0.5)
#     rep = treelstm.forward(inputs, indexes, trees)
#     print(rep[0].size())
#     print(rep[1].size())
#     print("test TDTreeLSTM OK")
#
#     print("test bitreelstm: ")
#     bitreelstm = BiTreeLSTM(10, 20, dropout_ratio=0.5)
#     rep = bitreelstm.forward(inputs, heads)
#     print(rep[0].size())
#     print(rep[1].size())
#
#
#
#
#
import torch
import torch.nn as nn
from mytree import *
import numpy as np
from torch.nn.utils.rnn import pad_sequence



class BiTreeLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, dropout_ratio):
        super(BiTreeLSTM, self).__init__()
        self.dropout_ratio = dropout_ratio
        self._input_dim = input_dim
        self._hidden_dim = hidden_dim


        self.dt_treelstm = DTTreeLSTM(input_dim, hidden_dim, dropout_ratio)
        self.td_treelstm = TDTreeLSTM(input_dim, hidden_dim, dropout_ratio)


    def forward(self, inputs, heads):
        max_length, batch_size, dim = inputs.size()
        assert dim == self._input_dim
        trees = []
        indexes = np.zeros((max_length, batch_size), dtype=np.int32)

        for b, head in enumerate(heads):
            root, tree = creatTree(head)
            root.traverse()
            for step, index in enumerate(root.order):
                indexes[step, b] = index
            trees.append(tree)


        dt_cells, dt_hiddens = self.dt_treelstm(inputs, indexes, trees)
        td_cells, td_hiddens = self.td_treelstm(inputs, indexes, trees)
        return torch.cat((dt_cells, td_cells), dim=2), torch.cat((dt_hiddens, td_hiddens), dim=2)

class DTTreeLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, dropout_ratio):
        super(DTTreeLSTM, self).__init__()
        self._input_dim = input_dim
        self._hidden_dim = hidden_dim
        self.ioux = nn.Linear(self._input_dim, 3 * self._hidden_dim)
        self.iouh = nn.Linear(self._hidden_dim, 3 * self._hidden_dim)
        self.fx = nn.Linear(self._input_dim, self._hidden_dim)
        self.fh = nn.Linear(self._hidden_dim, self._hidden_dim)

        self.dropout = nn.Dropout(dropout_ratio)

    def node_forward(self, xs, sum_child_cs, sum_child_hs):

        iou = self.ioux(xs) + self.iouh(sum_child_hs)
        i, o, u = torch.split(iou, iou.size(1) // 3, dim=1)
        i, o, u = torch.sigmoid(i), torch.sigmoid(o), torch.tanh(u)

        f = torch.sigmoid(
            self.fh(sum_child_hs) + self.fx(xs)
        )
        fc = torch.mul(f, sum_child_cs)

        c = torch.mul(i, u) + fc  # torch.sum(fc, dim=0, keepdim=True)
        h = torch.mul(o, torch.tanh(c))
        return c, h

    def forward(self, inputs, indexes, trees):
        max_length, batch_size, input_dim = inputs.size()
        steps_inputs = inputs[indexes, torch.arange(batch_size)]
        dt_state_c, dt_state_h = [], []
        for b in range(batch_size):
            dt_state_c.append({})
            dt_state_h.append({})

        for step in range(max_length):
            step_inputs = steps_inputs[step]
            sum_child_cs, sum_child_hs = [], []
            # step_inputs, sum_child_cs, sum_child_hs = [], [], []
            for b, tree in enumerate(trees):
                index = indexes[step, b]
                # print("child index:", [child.index for child in tree[index].children])
                # print("dt_state_c keys:", list(dt_state_c[b].keys()))
                if tree[index].children_num == 0:
                    sum_child_c = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
                    sum_child_h = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
                else:
                    child_c_list = [dt_state_c[b][child.index] for child in tree[index].children]
                    child_c = torch.stack(child_c_list, 0)
                    sum_child_c = torch.sum(child_c, dim=0)

                    child_h_list = [dt_state_h[b][child.index] for child in tree[index].children]
                    child_h = torch.stack(child_h_list, 0)
                    sum_child_h = torch.sum(child_h, dim=0)

                sum_child_cs.append(sum_child_c)
                sum_child_hs.append(sum_child_h)
            sum_child_cs = torch.stack(sum_child_cs, 0)
            sum_child_hs = torch.stack(sum_child_hs, 0)
            # when training, drop; when eval, not drop
            sum_child_hs = self.dropout(sum_child_hs)

            step_results = self.node_forward(step_inputs, sum_child_cs, sum_child_hs)
            for b in range(batch_size):
                index = indexes[step, b]
                dt_state_c[b][index], dt_state_h[b][index] = step_results[0][b], step_results[1][b]

        hiddens, cells = [], []
        for b in range(batch_size):
            tree = trees[b]  # 获取当前树
            actual_length = len(tree)  # 计算实际长度
            one_sent_cells = [dt_state_c[b].get(idx, torch.zeros((self._hidden_dim))) for idx in range(actual_length)]  # 使用实际长度
            one_sent_hiddens = [dt_state_h[b].get(idx, torch.zeros((self._hidden_dim))) for idx in range(actual_length)]  # 使用实际长度
            # cells.append(pad_sequence(one_sent_cells, batch_first=True))
            # hiddens.append(pad_sequence(one_sent_hiddens, batch_first=True))
            # 逐个将列表中的张量移到cuda:0上
            one_sent_cells = [tensor.to('cuda:0') for tensor in one_sent_cells]
            one_sent_hiddens = [tensor.to('cuda:0') for tensor in one_sent_hiddens]

            cells.append(torch.stack(one_sent_cells, 0))
            hiddens.append(torch.stack(one_sent_hiddens, 0))
        return torch.stack(cells, dim=0).transpose(0, 1), torch.stack(hiddens, dim=0).transpose(0, 1)

class TDTreeLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, dropout_ratio):
        super(TDTreeLSTM, self).__init__()
        self._input_dim = input_dim
        self._hidden_dim = hidden_dim
        self.ioux = nn.Linear(self._input_dim, 3 * self._hidden_dim)
        self.iouh = nn.Linear(self._hidden_dim, 3 * self._hidden_dim)
        self.fx = nn.Linear(self._input_dim, self._hidden_dim)
        self.fh = nn.Linear(self._hidden_dim, self._hidden_dim)

        self.dropout = nn.Dropout(dropout_ratio)

    def node_forward(self, xs, sum_child_cs, sum_child_hs):
        # print(xs.device, sum_child_hs.device)
        iou = self.ioux(xs) + self.iouh(sum_child_hs)
        i, o, u = torch.split(iou, iou.size(1) // 3, dim=1)
        i, o, u = torch.sigmoid(i), torch.sigmoid(o), torch.tanh(u)

        f = torch.sigmoid(
            self.fh(sum_child_hs) + self.fx(xs)
        )
        fc = torch.mul(f, sum_child_cs)

        c = torch.mul(i, u) + fc  # torch.sum(fc, dim=0, keepdim=True)
        h = torch.mul(o, torch.tanh(c))
        return c, h

    def forward(self, inputs, indexes, trees):
        # print("#### ", self.dropout.training)

        max_length, batch_size, input_dim = inputs.size()

        steps_inputs = inputs[indexes, torch.arange(batch_size)]
        dt_state_c, dt_state_h = [], []
        for b in range(batch_size):
            dt_state_c.append({})
            dt_state_h.append({})

        for step in reversed(range(max_length)):
            # step_inputs, parent_cs, parent_hs = [], [], []
            parent_cs, parent_hs = [], []
            step_inputs = steps_inputs[step]
            for b, tree in enumerate(trees):
                index = indexes[step, b]
                if tree[index].parent is None:
                    parent_c = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
                    parent_h = inputs.data.new(self._hidden_dim).fill_(0.).requires_grad_(False)
                else:
                    parent_c = dt_state_c[b][tree[index].parent.index]
                    parent_h = dt_state_h[b][tree[index].parent.index]
                parent_cs.append(parent_c)
                parent_hs.append(parent_h)

            parent_cs = torch.stack(parent_cs, 0)
            parent_hs = torch.stack(parent_hs, 0)

            parent_hs = self.dropout(parent_hs)
            step_results = self.node_forward(step_inputs, parent_cs, parent_hs)

            for b in range(batch_size):
                index = indexes[step, b]
                dt_state_c[b][index], dt_state_h[b][index] = step_results[0][b], step_results[1][b]

        hiddens, cells = [], []
        for b in range(batch_size):
            tree = trees[b]  # 获取当前树
            actual_length = len(tree)  # 计算实际长度
            one_sent_cells = [dt_state_c[b].get(idx, torch.zeros((self._hidden_dim))) for idx in range(actual_length)]  # 使用实际长度
            one_sent_hiddens = [dt_state_h[b].get(idx, torch.zeros((self._hidden_dim))) for idx in range(actual_length)]  # 使用实际长度
            # cells.append(pad_sequence(one_sent_cells, batch_first=True))
            # hiddens.append(pad_sequence(one_sent_hiddens, batch_first=True))
            one_sent_cells = [tensor.to('cuda:0') for tensor in one_sent_cells]
            one_sent_hiddens = [tensor.to('cuda:0') for tensor in one_sent_hiddens]

            cells.append(torch.stack(one_sent_cells, 0))
            hiddens.append(torch.stack(one_sent_hiddens, 0))
        return torch.stack(cells, dim=0).transpose(0, 1), torch.stack(hiddens, dim=0).transpose(0, 1)


if __name__ == '__main__':

    treelstm = DTTreeLSTM(10, 20, dropout_ratio=0.5)

    print("test node forward: ")
    xs = torch.randn((5, 10))
    sum_child_c = torch.randn((5, 20))
    sum_child_h = torch.randn((5, 20))
    rep = treelstm.node_forward(xs, sum_child_c, sum_child_h)
    print(rep[0].size())
    print(rep[1].size())
    print("test node forward OK")

    print("test forward: ")
    inputs = torch.randn((6, 2, 10))
    max_length, batch_size, dim = inputs.size()
    heads = [[-1, 2, 0, 2, 2, -1], [-1, 2, 0, 2, 2, -1]]
    heads = torch.tensor(heads, dtype=torch.long).to('cuda:0')
    trees = []
    indexes = np.zeros((max_length, batch_size), dtype=np.int32)
    for b, head in enumerate(heads):
        root, tree = creatTree(head)
        root.traverse()
        for step, index in enumerate(root.order):
            indexes[step, b] = index
        trees.append(tree)
    rep = treelstm.forward(inputs, indexes, trees)
    print(rep[0].size())
    print(rep[1].size())

    print("test forward OK")

    print("test DTTreeLSTM：")
    treelstm = DTTreeLSTM(10, 20, dropout_ratio=0.5)
    rep = treelstm.forward(inputs, indexes, trees)
    print(rep[0].size())
    print(rep[1].size())
    print("test DTTreeLSTM OK")

    print("test TDTreeLSTM：")
    treelstm = TDTreeLSTM(10, 20, dropout_ratio=0.5)
    rep = treelstm.forward(inputs, indexes, trees)
    print(rep[0].size())
    print(rep[1].size())
    print("test TDTreeLSTM OK")


    print("test bitreelstm: ")
    bitreelstm = BiTreeLSTM(10, 20, dropout_ratio=0.5)
    rep = bitreelstm.forward(inputs, heads)
    print(rep[0].size())
    print(rep[1].size())





