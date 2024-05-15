class Tree(object):
    def __init__(self, index):
        self.parent = None
        self.index = index
        self.children = list()
        self.children_num = 0
        self._depth = -1
        self.order = list()

    def add_child(self, child):
        """
        :param child: a Tree object represent the child
        :return:
        """
        child.parent = self
        self.children.append(child)
        self.children_num += 1

    def size(self):
        if hasattr(self, '_size'):
            return self._size
        count = 1
        for i in range(self.children_num):
            count += self.children[i].size()
        self._size = count
        return self._size



    def traverse(self):   #后序遍历
        if len(self.order) > 0:
            return self.order

        for i in range(self.children_num):
            order = self.children[i].traverse()
            self.order.extend(order)
        self.order.append(self.index)
        return self.order

def creatTree(heads):
    tree = []
    root = None
    for idx, head in enumerate(heads):
        tree.append(Tree(idx))

    for idx, head in enumerate(heads):
        if head == -1  and root is None:
            root = tree[idx]
            continue
        elif head==-1:
            continue

        assert head >= 0 and root is not None
        # print(head, idx, len(tree))
        tree[head].add_child(tree[idx])
    return root, tree

# def creatTree(heads):
#     tree = []
#     root = None
#     for idx, head in enumerate(heads):
#         tree.append(Tree(idx))
#
#     for idx, head in enumerate(heads):
#         if head == -1:
#             root = tree[idx]
#             continue
#         assert head >= 0 and root is not None
#         tree[head].add_child(tree[idx])
#     return root, tree

# def creatTree(heads):
#     tree = []
#     root = None
#     for idx, head in enumerate(heads):
#         tree.append(Tree(idx))
#
#     root_found = False  # 用于标记是否已找到根节点
#     for idx, head in enumerate(heads):
#         if head == -1:
#             if not root_found:  # 只处理第一个根节点标识
#                 root = tree[idx]
#                 root_found = True
#             continue
#         assert head >= 0 and root is not None
#         tree[head].add_child(tree[idx])
#     return root, tree


if __name__ == '__main__':
    root, tree = creatTree([-1, 2, 0, 2, 2])
    print(root.index)
    print(root.order)
    print(root.size())
    print(tree[root.index].traverse())   #后序遍历    print(root.size())


