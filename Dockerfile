FROM python:3.7.3

WORKDIR /opt
COPY ODBlib /opt/ODBlib/
COPY * /opt
RUN pip install -r requirements.txt

ENTRYPOINT [ "./run.sh" ]