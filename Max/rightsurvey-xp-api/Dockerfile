FROM python:3.6
WORKDIR /usr/src/app
COPY . /usr/src/app/
RUN apt-get update && apt-get install -y supervisor && mkdir -p /usr/src/app/logs && mkdir -p /var/log/supervisor\
 && curl -L https://github.com/edenhill/librdkafka/archive/v0.11.1.tar.gz | tar xzf -\
  && cd librdkafka-0.11.1/ && ./configure --prefix=/usr && make -j && make install\
   && cd /usr/src/app && pip install -r requirements.txt
COPY supervisor.conf /etc/supervisor/conf.d/supervisord.conf
EXPOSE 811
VOLUME /usr/src/app
CMD ["/usr/bin/supervisord"]