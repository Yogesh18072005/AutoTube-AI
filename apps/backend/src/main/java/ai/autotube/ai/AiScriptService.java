package ai.autotube.ai;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import java.util.List;
import java.util.Map;

@Service
public class AiScriptService {
    private final RestClient client;
    private final String apiKey;
    private final String model;

    public AiScriptService(
            RestClient.Builder builder,
            @Value("${autotube.ai.base-url}") String baseUrl,
            @Value("${autotube.ai.api-key:}") String apiKey,
            @Value("${autotube.ai.model:gpt-4o-mini}") String model) {
        this.client = builder.baseUrl(baseUrl).build();
        this.apiKey = apiKey;
        this.model = model;
    }

    public String generate(String topic, String language, String format, String tone, String audience) {
        if (apiKey == null || apiKey.isBlank()) {
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,
                    "OPENAI_API_KEY is not configured on the Java backend.");
        }
        String languageName = "hi".equalsIgnoreCase(language) ? "Hindi" : "English";
        String length = "long".equalsIgnoreCase(format) ? "6-10 minute YouTube video" : "45-60 second YouTube Short";
        String prompt = "Write an original " + length + " in " + languageName + " about " + topic
                + ". Audience: " + audience + ". Tone: " + tone
                + ". Include a strong hook, scene-by-scene narration, visual direction, and CTA. "
                + "Do not invent facts; flag claims that need source verification.";
        try {
            Map<?, ?> response = client.post()
                    .uri("/chat/completions")
                    .contentType(MediaType.APPLICATION_JSON)
                    .header("Authorization", "Bearer " + apiKey)
                    .body(Map.of(
                            "model", model,
                            "messages", List.of(
                                    Map.of("role", "system", "content", "You are an expert bilingual YouTube scriptwriter."),
                                    Map.of("role", "user", "content", prompt)),
                            "temperature", 0.7))
                    .retrieve()
                    .body(Map.class);
            List<?> choices = (List<?>) response.get("choices");
            Map<?, ?> first = (Map<?, ?>) choices.get(0);
            Map<?, ?> message = (Map<?, ?>) first.get("message");
            return String.valueOf(message.get("content"));
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "AI provider request failed.");
        }
    }
}