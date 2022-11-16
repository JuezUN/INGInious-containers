FROM    unjudge/uncode-c-base
LABEL   org.inginious.grading.name="HDL"

# Steps to install ghdl
COPY    ghdl-0.36.tar.gz /ghdl-0.36.tar.gz
RUN     tar -xvf ghdl-0.36.tar.gz && mv ghdl-0.36 ghdl
RUN     dnf -y install gcc make gcc-gnat zlib-devel
RUN     cd ghdl && ./configure --prefix=/usr/local && make && make install
# Steps to instal iverilog
# Copy source rpm source file
ADD     iverilog-10_2-2.el7.src.rpm /iverilog.rpm
RUN     dnf config-manager --enable powertools
# Libs to compile and rebuild rpm file for actual distro
RUN     dnf -y install rpm-build rpmdevtools tree
# links to older versions of requirements
RUN     cd /usr/lib64 && \
        ln -s libreadline.so.7 libreadline.so.6 && \
        rm -R libreadline.so.7
RUN     cd /usr/lib64 && \
        ln -s libhistory.so.7 libhistory.so.6 && \
        rm -R libhistory.so.7
# Libs to compile and rebuild rpm file for actual distro
RUN     dnf -y install autoconf bison bzip2-devel flex gcc-c++ gperf readline-devel


# Rebuild rpm file on /usr folder
RUN     rpmbuild --rebuild --define "_topdir /usr/rpmbuild" /iverilog.rpm

RUN     rpm -Uvh /usr/rpmbuild/RPMS/x86_64/iverilog-10_2-2.el8.x86_64.rpm && \
        rm /iverilog.rpm && \
        rm -R /usr/rpmbuild 

ADD     . /INGInious
RUN     cp -R /INGInious/grading/. /usr/lib/python3.9/site-packages/grading/
RUN     rm -R /INGInious
