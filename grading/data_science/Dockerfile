# DOCKER-VERSION 1.1.0

# Inherit from multilang container, which has all the needed scripts to launch tasks
FROM    unjudge/inginious-c-multilang
LABEL   org.inginious.grading.name="Data Science"

RUN     pip3.5 install numpy scipy pandas scikit-learn matplotlib scipy seaborn datascience cufflinks

RUN     yum clean all
