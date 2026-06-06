FROM maven:3.8-openjdk-11 AS build
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

FROM openjdk:11-jre-slim
WORKDIR /app
COPY --from=build /build/target/es-slice-gateway-1.0.0.jar app.jar
CMD ["java", "-jar", "app.jar"]
