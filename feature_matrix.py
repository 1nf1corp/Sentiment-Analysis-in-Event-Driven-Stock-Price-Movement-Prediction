#!/usr/bin/env python3
import json
import os
import datetime
import numpy as np

import nltk

from utils import generate_past_n_days, unify_word




def read_glove(we_file, w2i_file, concat=True):
    npz = np.load(we_file)
    W1 = npz['arr_0']
    W2 = npz['arr_1']
    with open(w2i_file) as f:
        word2idx = json.load(f)

    V = len(word2idx)
    if concat:
        We = np.hstack([W1, W2.T])
        print("We.shape:", We.shape)
        assert(V == We.shape[0])
    else:
        We = (W1 + W2.T) / 2
    return We

def padding(sentencesVec, keepNum):
    shape = sentencesVec.shape[0]
    ownLen = sentencesVec.shape[1]
    if ownLen < keepNum:
        return np.hstack((np.zeros([shape, keepNum-ownLen]), sentencesVec)).flatten()
    else:
        return sentencesVec[:, -keepNum:].flatten()

def gen_feature_matrix(word_embedding, word2idx, priceDt, max_words=60, mtype="test"):
    # step 2, build feature matrix for training data
    loc = './input/'
    input_files = [f for f in os.listdir(loc) if f.startswith('news_reuters.csv')]
    current_idx = 2
    dp = {} # only consider one news for a company everyday
    cnt = 0
    testDates = generate_past_n_days(100)
    shape = word_embedding.shape[1]
    features = np.zeros([0, max_words * shape])
    labels = []
    for file in input_files:
        for line in open(loc + file):
            line = line.strip().split(',')
            if len(line) != 5: continue
            ticker, name, day, headline, body = line
            if ticker not in priceDt: continue # skip if no corresponding company found
            if day not in priceDt[ticker]: continue # skip if no corresponding date found
            cnt += 1
            print(cnt)
            if mtype == "test" and day not in testDates: continue
            if mtype == "train" and day in testDates: continue
            # 2.1 tokenize sentense, check if the word belongs to the top words, unify the format of words
            tokens = nltk.word_tokenize(headline) + nltk.word_tokenize(body)
            tokens = [unify_word(t) for t in tokens]
            #tokens = [t for t in tokens if t in stopWords]
            #tokens = [t for t in tokens if t in topWords]
            # 2.2 create word2idx/idx2word list, and a list to count the occurence of words
            sentencesVec = np.zeros([shape, 0])
            for t in tokens:
                if t not in word2idx: continue
                sentencesVec = np.hstack((sentencesVec, np.matrix(word_embedding[word2idx[t]]).T))
            features = np.vstack((features, padding(sentencesVec, max_words)))
            labels.append(round(priceDt[ticker][day], 6))
    features = np.array(features)
    labels = np.matrix(labels)
    featureMatrix = np.concatenate((features, labels.T), axis=1)
    fileName = './input/featureMatrix_' + mtype + '.csv'
    np.savetxt(fileName, featureMatrix, fmt="%s")

def build(word_embedding, w2i_file, max_words=60):
    with open('./input/stockPrices.json') as data_file:    
        priceDt = json.load(data_file)
    with open(w2i_file) as data_file:    
        word2idx = json.load(data_file)
    
    gen_feature_matrix(word_embedding, word2idx, priceDt, max_words, "train")
    gen_feature_matrix(word_embedding, word2idx, priceDt, max_words, "test")


if __name__ == "__main__":
    we = './input/glove_model_50.npz'
    w2i_file = "./input/word2idx.json"
    word_embedding = read_glove(we, w2i_file)
    build(word_embedding, w2i_file, 30)