# Modeling VPC Emergence

This is the repository for the paper "word up: An Analogy-Based Approach to Predicting the Emergence of Novel Verb Particle Constructions".

### Jupyter notebooks
 * evaluation.ipynb: Experiments predicting novel VPC emergence (ranking methods and logistic regression evaluation).
 * vpc_corpus_stats.ipynb: Visualizations and statistics associated with the historical VPC corpus.
 
### Code for building the corpus
 * get_vpc_corpus.py: Builds the historical VPC corpus from the Google Syntactic Ngrams dataset.
 * extract_verbs.py: Extracts verbs for use in building the historical VPC corpus.
 * constants.py: Contains lists of particles in VPCs.
 
### Data
 * vpc_corpus.csv: The historical VPC corpus.
 * levin_1993_data.p: Levin verb classes. This is used in follow-up experiments not included in the paper.
