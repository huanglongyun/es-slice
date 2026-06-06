FROM maven:3.8-eclipse-temurin-11 AS build
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

FROM eclipse-temurin:11-jre
WORKDIR /app
COPY --from=build /build/target/es-slice-gateway-1.0.0.jar app.jar
CMD ["java", "-jar", "app.jar"]
