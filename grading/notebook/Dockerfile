# DOCKER-VERSION 1.1.0
# Inherit from the base container, which has all the needed scripts to launch tasks
FROM    unjudge/uncode-c-base
LABEL   org.inginious.grading.name="Notebook"

# Add python modules and OK grading module
RUN     pip3 install --upgrade pip
RUN     pip3 install nbconvert==6.0.7 pandas==1.1.5 numpy==1.19.5 matplotlib==3.2.2 scipy==1.4.1 scikit-learn==0.22.2.post1 \
        seaborn==0.11.1 datascience==0.10.6 plotly==4.4.1 cufflinks bokeh==2.1.1 tabulate nltk==3.4.5 tensorflow==2.4.0 \
        Keras statsmodels==0.10.2 antlr4-python3-runtime geopandas==0.9.0
RUN     pip3 install --no-cache-dir --upgrade okpy

# Necessary for qiskit
RUN     yum install -y gcc gcc-c++
RUN     pip3 install qiskit[visualization]==0.23.0

# Download nltk data
# RUN python3 -m nltk.downloader -d /usr/local/share/nltk_data all

RUN     chown -R worker:worker /root

RUN     yum clean all

ADD     . /INGInious
RUN     cp -R /INGInious/grading/.  /usr/lib/python3.6/site-packages/grading/
RUN     rm -R /INGInious
