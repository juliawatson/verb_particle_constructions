import os
import subprocess
from tqdm import tqdm
from collections import defaultdict, Counter


NOUN_LABELS = ['NN', 'NNS', 'NNP', 'NNPS']
VERB_LABELS = ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']


def get_file_range(local_path):
    try:
        start = subprocess.check_output(['head', '-1', local_path]).decode('ascii')
        start_word = start.split('\t')[0]
    except UnicodeDecodeError:
        start_word = None
    try:
        end = subprocess.check_output(['tail', '-1', local_path]).decode('ascii')
        end_word = end.split('\t')[0]
    except UnicodeDecodeError:
        end_word = None
    return start_word, end_word
    
    
def get_formatted_str(i):
    i = str(i)
    if len(i) == 1:
        i = '0' + i
    return i
    
    
def get_first_word(line):
    i = 0
    while line[i] != '\t' and i < len(line):
        i += 1
    return line[:i]


def download_file(i, file_type="nodes"):
    i = get_formatted_str(i)
    local_path = 'google_ngrams/{}.{}-of-99'.format(file_type, i)
    # download file if it does not exist
    if not os.path.isfile(local_path):
        print('downloading file {}'.format(i))
        os.system('wget -O google_ngrams/{}.{}-of-99.gz http://commondatastorage.googleapis.com/books/syntactic-ngrams/eng/{}.{}-of-99.gz'.format(file_type, i, file_type, i))
        os.system('gunzip google_ngrams/{}.{}-of-99.gz'.format(file_type, i))
    return local_path


def get_by_tags(output_path, tags, min_total_count=10000):
    verb_to_count = defaultdict(lambda: defaultdict(int))
    for i in range(12, 99):  # 12 is where the non-number words start
        local_path = download_file(i)
        
        # skip file if we don't want to check for any words from this range
        start_word, end_word = get_file_range(local_path)
        print("file {}: '{}' to '{}'".format(i, start_word, end_word))
        if not start_word or not end_word:
            continue
        
        with open(local_path, 'r') as f:
            for line in tqdm(f):
                first_word = get_first_word(line)
                if not first_word[0].isalpha():
                    continue
                ngram = get_first_word(line[len(first_word) + 1:])
                count = int(get_first_word(line[len(first_word) + len(ngram) + 2:]))
                if count < min_total_count:
                    continue
                
                pos = ngram.split('/')[1]
                if pos not in tags:
                    continue
                # verb_to_count[first_word] += count
                line = line.split('\t')

                ### START: Copied from get_vpc_corpus.py
                year_counts = line[3:]
                # print(year_counts)
                # vn_tuple = (first_word, arg)
                for year_count in year_counts:
                    year_count = year_count.split(',')
                    if len(year_count) != 2:
                        break
                    year, count = year_count
                    count = int(count.strip())
                    verb_to_count[first_word][str((int(year) // 10) * 10)] += count
                ### END: Copied from get_vpc_corpus.py

        print("removing {}".format(local_path))
        os.remove(local_path)

    with open(output_path, "w") as f:            
        ### START: Copied from get_vpc_corpus.py
        for word, year_to_count in verb_to_count.items():
            year_counts = []
            total_count = sum(list(year_to_count.values()))
            for year in sorted(list(year_to_count.keys())):
                year_counts.append(','.join([str(year), str(year_to_count[year])]))
            first_occurrence = min(year_to_count.keys())
            f.write('\t'.join([word, str(total_count), str(first_occurrence)] + year_counts) + '\n')
        ### END: Copied from get_vpc_corpus.py



if __name__ == "__main__":
    get_by_tags("verb_counts.csv", VERB_LABELS)
