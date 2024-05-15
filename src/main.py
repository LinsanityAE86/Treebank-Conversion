import sys
#sys.path.extend(["../src/", "../", "./"])
import random
import time
import argparse
#from tag_orith_parser import Parser
from parser1 import Parser
from config import Configurable
import torch
import numpy as np
import os
if __name__ == '__main__':
    torch.backends.cudnn.enable = True
    torch.backends.cudnn.benchmark = True
    default_seed = int(time.time())
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--exp_des', default='des="conll-bucketing-pad"')
    argparser.add_argument('--config_file', default='../exp-conll-all/config.txt')
    argparser.add_argument('--random_seed', type=int, default=default_seed)
    # argparser.add_argument('--thread', default=4, type=int, help='thread num')

    args, extra_args = argparser.parse_known_args()
    conf = Configurable(args.config_file, extra_args)
    # cudaNo = conf.cudaNo
    # os.environ["CUDA_VISIBLE_DEVICES"] = cudaNo
 
    all_seeds = [args.random_seed]
    random.seed(all_seeds[0])
    for i in range(3):
        all_seeds.append(random.randint(1, 987654321))
    np.random.seed(2022)
    torch.cuda.manual_seed(all_seeds[2])
    torch.manual_seed(all_seeds[3])
    print('random_seeds = ', all_seeds, flush=True)

    torch.set_num_threads(4)  # run with CPU, then use multi-thread? What does this mean?

    parser = Parser(conf, label_dict_size=113)
    parser.run()

