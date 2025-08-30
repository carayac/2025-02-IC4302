FROM spark:3.5.1-scala2.12-java11-ubuntu
# https://stackoverflow.com/questions/27717379/spark-how-to-run-spark-file-from-spark-shell

WORKDIR /app

COPY app/. .
RUN /opt/spark/bin/spark-shell -i functions.scala -i test.scala

#CMD [ "tail", "-f", "/dev/null" ]
CMD ["spark-shell", "-i", "functions.scala", "-i", "app.scala"]
