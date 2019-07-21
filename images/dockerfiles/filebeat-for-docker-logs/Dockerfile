FROM docker.elastic.co/beats/filebeat:7.2.0
# Copy our custom configuration file
COPY filebeat.yml ./filebeat.yml
USER root
# Create a directory to map volume with all docker log files
RUN mkdir /usr/share/filebeat/dockerlogs
RUN chown -R root /usr/share/filebeat/
RUN chmod -R go-w /usr/share/filebeat/
