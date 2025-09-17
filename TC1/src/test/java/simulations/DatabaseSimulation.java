import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;

import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.*;

public class DatabaseSimulation extends Simulation {

    // Configuración del protocolo HTTP
    HttpProtocolBuilder httpProtocol = http
        .baseUrl("http://localhost:30080") // ⚠️ cambia al NodePort de tu API en Kubernetes
        .acceptHeader("application/json");

    // Escenario de health check
    ScenarioBuilder health = scenario("Health Check")
        .exec(http("Health endpoint").get("/health").check(status().is(200)));

    // Escenarios con bases de datos
    ScenarioBuilder animalesMariaDb = scenario("Animales en MariaDB")
        .exec(http("MariaDB Query").get("/animales?db=mariadb").check(status().is(200)));

    ScenarioBuilder animalesPostgres = scenario("Animales en PostgreSQL")
        .exec(http("Postgres Query").get("/animales?db=postgres").check(status().is(200)));

    ScenarioBuilder animalesElastic = scenario("Animales en Elasticsearch")
        .exec(http("Elastic Query").get("/animales?db=elasticsearch").check(status().is(200)));

    // Escenarios con cache
    ScenarioBuilder animalesRedis = scenario("Animales en MariaDB con Redis")
        .exec(http("MariaDB Redis").get("/animales?db=mariadb&cache=redis").check(status().is(200)));

    ScenarioBuilder animalesMemcached = scenario("Animales en Postgres con Memcached")
        .exec(http("Postgres Memcached").get("/animales?db=postgres&cache=memcached").check(status().is(200)));

    {
        // Configuración de los tests (15 min = 900 segundos)
        setUp(
            health.injectOpen(atOnceUsers(5)),
            animalesMariaDb.injectOpen(rampUsers(100).during(9)),
            animalesPostgres.injectOpen(rampUsers(100).during(9)),
            animalesElastic.injectOpen(rampUsers(100).during(9)),
            animalesRedis.injectOpen(rampUsers(100).during(9)),
            animalesMemcached.injectOpen(rampUsers(100).during(9))
        ).protocols(httpProtocol);
    }
}
