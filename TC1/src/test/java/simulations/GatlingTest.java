import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;

import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.*;
import java.time.Duration;

public class GatlingTest extends Simulation {
    int users = 100;
    int time = 900; //tiempo en segundos

    HttpProtocolBuilder httpProtocol = http
        .baseUrl("http://localhost:30080") // 
        .acceptHeader("application/json");

    // Escenarios separados
    ScenarioBuilder health = scenario("Health Check")
        .exec(http("Health endpoint").get("/health").check(status().is(200)));

    ScenarioBuilder animales = scenario("Animales")
        .exec(http("Animales endpoint").get("/animales").check(status().is(200)));

    ScenarioBuilder colores = scenario("Colores")
        .exec(http("Colores endpoint").get("/colores").check(status().is(200)));

    // Escenario aleatorio entre animales y colores
    String[] endpoints = { "/animales", "/colores" };

    ScenarioBuilder randomCalls = scenario("Random Calls")
        .during(Duration.ofMinutes(15))
        .on(
            exec(session -> {
                String endpoint = endpoints[(int)(Math.random() * endpoints.length)];
                return session.set("endpoint", endpoint);
            })
            .exec(http("Random Query")
                .get("#{endpoint}")
                .check(status().is(200)))
        );

    {
        setUp(
            health.injectOpen(atOnceUsers(5)),
            randomCalls.injectOpen(rampUsers(users).during(time))
        ).protocols(httpProtocol);
    }
}
