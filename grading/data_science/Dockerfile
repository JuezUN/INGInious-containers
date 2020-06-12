# DOCKER-VERSION 1.1.0

# Inherit from multilang container, which has all the needed scripts to launch tasks
FROM    unjudge/inginious-c-multilang
LABEL   org.inginious.grading.name="Data Science"

RUN     pip3.5 install pandas numpy scipy scikit-learn datascience cufflinks tabulate nltk==3.4.5

RUN     yum clean all
