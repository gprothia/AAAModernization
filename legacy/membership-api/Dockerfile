# Runs the legacy service unchanged in a GKE sandbox, for the characterisation harness only.
FROM maven:3.8-openjdk-8 AS build
WORKDIR /src
COPY pom.xml .
COPY src ./src
RUN mvn -q package

FROM tomcat:7-jre8
# The harness freezes the clock (FAKETIME, set in deploy/sandbox/legacy.yaml) so refunds and
# renewals give the same answer on every run. The application code is not changed.
RUN apt-get update && apt-get install -y --no-install-recommends faketime && rm -rf /var/lib/apt/lists/*
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1
COPY --from=build /src/target/membership-api-2.7.3.war /usr/local/tomcat/webapps/ROOT.war
COPY db/seed.sql /seed.sql
EXPOSE 8080
