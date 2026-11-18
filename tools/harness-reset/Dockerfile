FROM eclipse-temurin:8-jre
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
ADD https://repo1.maven.org/maven2/com/h2database/h2/1.4.200/h2-1.4.200.jar /h2.jar
COPY reset.py /reset.py
# reset.sql = DROP ALL OBJECTS; followed by legacy/membership-api/db/seed.sql (copied at build)
COPY reset.sql /reset.sql
CMD ["python3", "/reset.py"]
