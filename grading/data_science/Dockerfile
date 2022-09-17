# DOCKER-VERSION 1.1.0

# Inherit from multilang container, which has all the needed scripts to launch tasks
FROM    unjudge/inginious-c-multilang
LABEL   org.inginious.grading.name="Data Science"

RUN     pip3.9 install --upgrade pip
RUN     pip3.9 install pandas==1.3.5 numpy==1.21.6 scipy==1.7.3 scikit-learn==1.0.2 datascience==0.17.5 cufflinks==0.17.3 tabulate==0.8.10 nltk==3.4.5

RUN     dnf clean all
