# DOCKER-VERSION 1.1.0

# Inherit from the base container, which has all the needed scripts to launch tasks
FROM    unjudge/uncode-c-base
LABEL org.inginious.grading.name="Notebook"


# Add python modules and OK grading module
RUN pip3.5 install jupyter pandas numpy matplotlib scipy scikit-learn seaborn datascience
RUN pip3.5 install --no-cache-dir --upgrade okpy

RUN chown -R worker:worker /root

RUN yum clean all

ADD . /INGInious
RUN cp -R /INGInious/grading/.  /usr/lib/python3.5/site-packages/grading/
RUN rm -R /INGInious
