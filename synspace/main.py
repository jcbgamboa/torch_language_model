from __future__ import print_function
import argparse
import torch
import torch.utils.data
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
from torchvision import datasets, transforms
import torch.nn.functional as F
from time import strftime, gmtime, time

import spacy


import os
import sys
import pickle
import numpy as np


from model import LanguageModel

def log(x):
    print(x)

def get_time(self):
    return strftime('%Y-%m-%d %H:%M:%S', gmtime())

def parse_args():
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument('--batch_size', type=int, default=128, metavar='N',
                        help='input batch size for training (default: 128)')
    parser.add_argument('--nb_epoch', type=int, default=10, metavar='N',
                        help='number of epochs to train (default: 10)')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='enables CUDA training')
    parser.add_argument('--seed', type=int, default=1, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument('--language', type=str, default='en',
                        help='Language code to be used. Default: "en";'
                             ' Accepted: "en", "de".')
    parser.add_argument('--validation_split', type=float, default=1,
                        help='how much of the training set should be used for '
                             'validation')
    args = parser.parse_args()
    args.cuda = not args.no_cuda and torch.cuda.is_available()
    return args


def main(args):
    # Initializes the random seed
    torch.manual_seed(args.seed)
    if args.cuda:
        torch.cuda.manual_seed(args.seed)

    # "Builds" the model and sends it to the GPU
    model = LanguageModel()
    if args.cuda:
        model.cuda()

    # Initializes spaCy
    nlp = spacy.load(args.language)

    # Defines a new optimizer
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    # Run
    train(model, optimizer, args, nlp)
    test(model, optimizer, args, nlp)

def load_dataset(self, which_dataset='train', load_column_vecs=False):
    file_name = 'word_synonym_antonym.' + which_dataset
    file_path = os.path.join('data', self.conf['dataset_name'], file_name)
    triples = pickle.load(open(file_path, 'rb'))

    words_vec    = torch.Tensor([self.nlp.vocab[i[0]].vector for i in triples])
    synonyms_vec = torch.Tensor([self.nlp.vocab[i[1]].vector for i in triples])
    antonyms_vec = torch.Tensor([self.nlp.vocab[i[2]].vector for i in triples])

    if load_column_vecs:
        words_vec    = words_vec.unqueeze(1)
        synonyms_vec = synonyms_vec.unqueeze(1)
        antonyms_vec = antonyms_vec.unqueeze(1)

    words    = torch.from_numpy(np.array([i[0] for i in triples]))
    synonyms = torch.from_numpy(np.array([i[1] for i in triples]))
    antonyms = torch.from_numpy(np.array([i[2] for i in triples]))

    return words_vec, synonyms_vec, antonyms_vec, words, synonyms, antonyms


def loss_function(x, distance, args):
    # First, separate the input
    target_word, synonym, antonym = x

    # Calculate the distance between all elements
    good_distance = distance(target_word, synonym)
    bad_distance = distance(target_word, antonym)

    loss = F.relu(args.margin - good_distance + bad_distance)
    return loss


def train(model, optimizer, nlp, args):
    batch_size = args.batch_size
    nb_epoch = args.nb_epoch
    validation_split = args.validation_split

    words_vec, synonyms_vec, antonyms_vec, words, synonyms, antonyms = \
                                                        load_dataset()
    assert len(words_vec) == len(synonyms_vec) == len(antonyms_vec)

    log('Began training at %s on %d samples' % (get_time(), len(words_vec)))

    val_loss = {'loss': 1., 'epoch': 0}

    good = nlp.vocab['good'].vector[np.newaxis, :]
    bad = nlp.vocab['bad'].vector[np.newaxis, :]

    # Maybe it is best not to care about epochs
    for i in range(1, nb_epoch+1):
        print('Fitting epoch %d' % i, file=sys.stderr)



        # hist = self.model.fit([words_vec, synonyms_vec, antonyms_vec], nb_epoch=1,
        #                   batch_size=batch_size,
        #                   validation_split=validation_split, verbose=1)

        data = Variable(data)
        if args.cuda:
            data = data.cuda()
        x = model(data)
        # loss = loss_function(x, distance, args)
        # loss.backward()
        # train_loss += loss.data[0]
        # optimizer.step()
        # if batch_idx % args.log_interval == 0:
        #     print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
        #         epoch, batch_idx * len(data), len(train_loader.dataset),
        #         100. * batch_idx / len(train_loader),
        #         loss.data[0] / len(data)))
        #
        # This should happen by the end of an epoch
        # print('====> Epoch: {} Average loss: {:.4f}'.format(
        #     epoch, train_loss / len(train_loader.dataset)))

    return val_loss

def test(model, optimizer, nlp, args):
    model.eval()
    test_loss = 0
    for data, _ in test_loader:
        if args.cuda:
            data = data.cuda()
        data = Variable(data, volatile=True)
        recon_batch, mu, logvar = model(data)
        test_loss += loss_function(recon_batch, data, mu, logvar).data[0]

    test_loss /= len(test_loader.dataset)
    print('====> Test set loss: {:.4f}'.format(test_loss))