from collections import defaultdict
import constants
import extract_verbs
import os
from tqdm import tqdm
import lemminflect

# import spacy
# from nltk.stem import PorterStemmer
# ps = PorterStemmer()
# nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])


def load_wordlist(data_path):
    result = {}
    with open(data_path, "r") as f:
        for line in f:
            line = line.strip().split(",")
            result[line[0]] = float(line[1])
    return result


SEED_VERBS = load_wordlist("verb_counts.csv")
SEED_PARTICLES = constants.PARTICLES


def write_args_to_file(output_file, arguments, write_all=True,
                       cutoff=None, verbs_seen=[], min_count=25):
    words_written = set()
    v_n_to_pop = set()
    with open(output_file, 'a') as f:
        for word, year_to_count in arguments.items():
            v, n = word
            if (cutoff is not None and
                any([v_inflect >= cutoff for v_inflect in get_inflections(v)])):
                continue
            if not write_all:
                if v not in words_written:
                    words_written.add(v)
                v_n_to_pop.add((v, n))
            year_counts = []
            total_count = sum(list(year_to_count.values()))
            if total_count < min_count:
                continue
            for year in sorted(list(year_to_count.keys())):
                year_counts.append(','.join([str(year), str(year_to_count[year])]))
            f.write('\t'.join([v, n, str(total_count)] + year_counts) + '\n')
    for w in v_n_to_pop:
        arguments.pop(w)
    return arguments, words_written


def extract_particle(ngram, target_verb):
    # only return something if the head is a verb
    verb_index = None
    ngram = [item.split('/') for item in ngram.split(' ')]
    for i, item in enumerate(ngram):
        if item[3] == '0':
            assert item[0] == target_verb
            verb_index = i + 1
            break

    # Skip double preposisions (e.g. "run up onto")
    for i in range(verb_index + 1, len(ngram) - 1):
        item = ngram[i]
        if item[0] in SEED_PARTICLES:
            return None
            
    # Only include cases where the final token in the verb phrase is one of
    # the seed particles. This is a high precision filtering approach.
    if (ngram[-1][3] == str(verb_index) and
        ngram[-1][0] in SEED_PARTICLES and
        ngram[-1][2] == "prt"):
        return ngram[-1][0]
    return None
    
    
def get_stem(token):
    # return nlp(token)[0].lemma_
    # return ps.stem(token)
    return lemminflect.getLemma(token, "VERB")[0]
    
    
def get_inflections(token):
    result = set()
    for key, value in lemminflect.getAllInflections(token).items():
        result.update(value)
    return result


def get_vpc_corpus(output_file, min_year=1800):
    """
    Generate a corpus at output_file of the format:
        verb   particle   year_counts
    
    where year_counts is of the format (tab-separated):
    1800,3  1810,12 1820,15 ....
    """
    # word list is seed verbs plus inflected seed verbs
    word_list = SEED_VERBS
    word_list = sorted(word_list)
    verbs_seen = set()
    verbs_written = set()
    
    vn_to_year_to_count = defaultdict(dict)
    for i in range(99):
    # for i in [76]:
        local_path = extract_verbs.download_file(i, file_type="verbargs")
        
        # skip file if we don't want to check for any words from this range
        start_word, end_word = extract_verbs.get_file_range(local_path)
        print("file {}: '{}' to '{}'".format(i, start_word, end_word))
        if start_word and end_word:
            while word_list[0] < start_word and len(word_list) > 1:
                word_list = word_list[1:]
            if word_list[0] > end_word:
                os.system('rm {}'.format(local_path))
                continue

        with open(local_path, 'r') as f:
            for line in tqdm(f):
                first_word = extract_verbs.get_first_word(line)
                if not first_word[0].isalpha():
                    continue
                while word_list[0] < first_word and len(word_list) > 1:
                    word_list = word_list[1:]
                if word_list[0] == first_word:
                    line = line.split('\t')
                    ngram = line[1]
                    arg = extract_particle(ngram, first_word)
                    # print(ngram, "=>", first_word, arg)
                    if arg is not None:
                        # print(ngram)
                        first_word_inflected = first_word
                        first_word = get_stem(first_word)
                        assert first_word not in verbs_written, f"Verb is already written: {first_word} ({first_word_inflected})"
                        year_counts = line[3:]
                        vn_tuple = (first_word, arg)
                        for year_count in year_counts:
                            year_count = year_count.split(',')
                            if len(year_count) != 2:
                                break
                            year, count = year_count
                            count = int(count.strip())
                            if year in vn_to_year_to_count[vn_tuple]:
                                vn_to_year_to_count[vn_tuple][str((int(year) // 10) * 10)] += count
                            else:
                                vn_to_year_to_count[vn_tuple][str((int(year) // 10) * 10)] = count
        vn_to_year_to_count, new_verbs_written = write_args_to_file(
            output_file, vn_to_year_to_count, write_all=False,
            cutoff=get_stem(end_word)[:2], verbs_seen=verbs_seen)
        verbs_written.update(new_verbs_written)
        os.system('rm {}'.format(local_path))

    write_args_to_file(output_file, vn_to_year_to_count, write_all=True)
    
    
if __name__ == "__main__":
    get_vpc_corpus("vpc_corpus.csv")