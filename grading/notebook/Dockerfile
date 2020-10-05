# DOCKER-VERSION 1.1.0
# Inherit from the base container, which has all the needed scripts to launch tasks
FROM    unjudge/uncode-c-base
LABEL   org.inginious.grading.name="Notebook"

# Add python modules and OK grading module
RUN     pip3 install --upgrade pip
RUN     pip3 install jupyter pandas==1.0.5 numpy==1.18.5 matplotlib scipy scikit-learn seaborn datascience \
        plotly cufflinks bokeh tabulate nltk==3.4.5 tensorflow Keras statsmodels antlr4-python3-runtime qiskit
RUN     pip3 install --no-cache-dir --upgrade okpy

# Download nltk data
# RUN python3 -m nltk.downloader -d /usr/local/share/nltk_data all

RUN     chown -R worker:worker /root

RUN     yum clean all

ADD     . /INGInious
RUN     cp -R /INGInious/grading/.  /usr/lib/python3.6/site-packages/grading/
RUN     rm -R /INGInious
