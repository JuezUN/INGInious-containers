# DOCKER-VERSION 1.1.0

# Inherit from the base container, which has all the needed scripts to launch tasks
FROM    uncode
LABEL org.inginious.grading.name="Python"

ADD . /INGInious
RUN cp -R /INGInious/grading/.  /usr/lib/python3.5/site-packages/grading/
RUN rm -R /INGInious
