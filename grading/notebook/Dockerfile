# DOCKER-VERSION 1.1.0
# Inherit from the base container, which has all the needed scripts to launch tasks
FROM    unjudge/uncode-c-base
LABEL   org.inginious.grading.name="Notebook"

# Necessary for qiskit
RUN     dnf install -y gcc gcc-c++
# Add python modules and OK grading module
RUN     pip3.9 install --upgrade pip
RUN     pip3.9 install nbconvert==7.0.0 pandas==1.5.3 numpy==1.22.4 matplotlib==3.7.1 scipy==1.10.1 scikit-learn==1.2.2 \
        seaborn==0.12.2 datascience==0.17.6 plotly==5.13.1 cufflinks==0.17.3 bokeh==3.1.1 tabulate==0.9.0 nltk==3.8.1 tensorflow==2.12.0 \
        Keras==2.12 statsmodels==0.13.5 antlr4-python3-runtime geopandas==0.13.2 cassandra-driver==3.28.0 pymongo==4.4.1 

#Last version of okpy is 1.18.1 on 2020
RUN     pip3.9 install --no-cache-dir --upgrade okpy==1.18.1
# Necessary for okpy==1.18.1
RUN     pip3.9 install requests==2.22.0
# Installing qiskit
RUN     pip3.9 install qiskit[visualization]==0.44.0

#Installing Dask
RUN     pip3.9 install dask[complete]==2023.7.1 dask_ml==2023.3.24
# Installing unidecode
RUN     pip3.9 install Unidecode==1.3.6
# Installing gensim
RUN     pip3.9 install gensim==4.2.0
# Installing spacy
RUN     pip3.9 install spacy==3.4.3
# Download spacy model es
RUN     python3 -m spacy download es_core_news_sm
# Installing pyarrow
RUN     pip3.9 install pyarrow==10.0.1
# Installing wordcloud
RUN     pip3.9 install wordcloud==1.8.2.2

#Uninstall attrs and jsonschema in order to install correct versions for okpy
RUN     pip3.9 uninstall attrs jsonschema -y

# Necessary for okpy==1.18.1
RUN     pip3.9 install attrs==19.3.0 pipdeptree jsonschema==2.6.0

#You can install In order to debug libs versions problems
#RUN     pip3.9 install pipdeptree


# Download nltk data
# RUN python3 -m nltk.downloader -d /usr/local/share/nltk_data all

RUN     chown -R worker:worker /root

RUN     dnf clean all

ADD     . /INGInious
RUN     cp -R /INGInious/grading/.  /usr/lib/python3.9/site-packages/grading/
RUN     rm -R /INGInious
