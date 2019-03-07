FROM leochan007/python36

LABEL MAINTAINER leo chan <leochan007@163.com>

ENV DEBIAN_FRONTEND noninteractive

RUN pip3 install -U bson pymongo pandas numpy xlsxwriter pyyaml

COPY src /root

WORKDIR /root

CMD python gen_report.py
