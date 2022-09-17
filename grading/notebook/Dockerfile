# DOCKER-VERSION 1.1.0
# Inherit from the base container, which has all the needed scripts to launch tasks
FROM    unjudge/uncode-c-base
LABEL   org.inginious.grading.name="Notebook"

# Necessary for qiskit
RUN     dnf install -y gcc gcc-c++
# Add python modules and OK grading module
RUN     pip3.9 install --upgrade pip
RUN     pip3.9 install nbconvert==7.0.0 pandas==1.3.5 numpy==1.21.6 matplotlib==3.5.3 scipy==1.7.3 scikit-learn==1.0.2 \
        seaborn==0.11.2 datascience==0.17.5 plotly==5.5.0 cufflinks==0.17.3 bokeh==2.3.3 tabulate==0.8.10 nltk==3.7 tensorflow==2.8.2 \
        Keras==2.8.0 statsmodels==0.12.2 antlr4-python3-runtime geopandas==0.9.0 

#Last version of okpy is 1.18.1 on 2020
RUN     pip3.9 install --no-cache-dir --upgrade okpy==1.18.1
# Necessary for okpy==1.18.1
RUN     pip3.9 install requests==2.22.0
# Installing qiskit
RUN     pip3.9 install qiskit[visualization]==0.37.2

# Download nltk data
# RUN python3 -m nltk.downloader -d /usr/local/share/nltk_data all

RUN     chown -R worker:worker /root

RUN     dnf clean all

ADD     . /INGInious
RUN     cp -R /INGInious/grading/.  /usr/lib/python3.9/site-packages/grading/
RUN     rm -R /INGInious
