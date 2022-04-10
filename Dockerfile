FROM ubuntu:jammy

RUN mkdir -p /opt/birdword/

ADD ./* /opt/birdword/

RUN apt update

RUN apt install -y python3-pip

RUN pip3 install -r /opt/birdword/requirements.txt

CMD ["python3", "/opt/birdword/birdword.py"]
