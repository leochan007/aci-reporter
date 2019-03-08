FROM  leochan007/reporter_base

LABEL MAINTAINER leo chan <leochan007@163.com>

ENV DEBIAN_FRONTEND noninteractive

COPY src /root

WORKDIR /root

CMD python3 gen_report.py; tail -f /dev/null
