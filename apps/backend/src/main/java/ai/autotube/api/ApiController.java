package ai.autotube.api;

import ai.autotube.ai.AiScriptService;
import ai.autotube.records.RecordService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.time.Instant;
import java.util.*;

@RestController
public class ApiController {
    private final RecordService records;
    private final AiScriptService ai;

    public ApiController(RecordService records, AiScriptService ai) {
        this.records = records;
        this.ai = ai;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "ok", "service", "autotube-java-api", "version", "1.0.0");
    }

    @GetMapping("/api/v1/config")
    public Map<String, Object> config() {
        return Map.of(
                "languages", List.of(Map.of("value","en","label","English"), Map.of("value","hi","label","Hindi")),
                "formats", List.of(Map.of("value","short","label","YouTube Shorts"), Map.of("value","long","label","Long-form")),
                "modules", List.of("dashboard","channels","research","scripts","voice","media","editor","thumbnails","seo","approval","publishing","analytics","automation","settings"),
                "publishing_requires_approval", true);
    }

    @GetMapping("/api/v1/records")
    public List<Map<String,Object>> list(@RequestParam(required = false) String kind) {
        return records.list(kind);
    }

    @GetMapping("/api/v1/settings")
    public Map<String,Object> settings() {
        List<Map<String,Object>> saved = records.list("settings");
        if (saved.isEmpty()) return defaultSettings();
        return new LinkedHashMap<>((Map<String,Object>) saved.get(0).get("data"));
    }

    @PutMapping("/api/v1/settings")
    public Map<String,Object> updateSettings(@RequestBody Map<String,Object> body) {
        Map<String,Object> merged = defaultSettings();
        merged.putAll(body);
        List<Map<String,Object>> saved = records.list("settings");
        if (saved.isEmpty()) {
            return (Map<String,Object>) records.create("settings", "workspace_settings", merged).get("data");
        }
        return (Map<String,Object>) records.change(String.valueOf(saved.get(0).get("id")), "workspace_settings", merged).get("data");
    }

    private Map<String,Object> defaultSettings() {
        Map<String,Object> defaults = new LinkedHashMap<>();
        defaults.put("channel_name", "");
        defaults.put("default_language", "en");
        defaults.put("default_format", "short");
        defaults.put("ai_provider", "none");
        defaults.put("tts_provider", "none");
        return defaults;
    }


    @PostMapping("/api/v1/ideas")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> idea(@RequestBody Map<String,Object> body) {
        requireTopic(body);
        return records.create("idea", "idea", body);
    }

    @PostMapping("/api/v1/research")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> research(@RequestBody Map<String,Object> body) {
        requireTopic(body);
        String topic = String.valueOf(body.get("topic"));
        Map<String,Object> result = new LinkedHashMap<>(body);
        result.put("research_status", "needs_provider");
        result.put("angle", "What beginners should understand about " + topic);
        result.put("suggested_hooks", List.of("The truth about " + topic, "What beginners misunderstand about " + topic));
        result.put("source_notes", List.of());
        result.put("provider_message", "Connect a research provider for live sources and trend signals.");
        return records.create("research", "researched", result);
    }

    @PostMapping("/api/v1/scripts")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> script(@RequestBody Map<String,Object> body) {
        requireTopic(body);
        String topic = String.valueOf(body.get("topic"));
        String hook = "hi".equals(body.get("language"))
                ? "Kya aap jaante hain " + topic + " asal mein kaise kaam karta hai?"
                : "Have you ever wondered how " + topic + " actually works?";
        Map<String,Object> result = new LinkedHashMap<>(body);
        result.put("hook", hook);
        result.put("full_text", hook + "\n\nLet's break down " + topic + " in simple terms.\n\nFollow for more practical AI and technology explainers.");
        result.put("generation_mode", "template_fallback");
        result.put("provider_message", "Starter draft. Use /api/v1/scripts/generate for AI-generated content.");
        return records.create("script", "script_draft", result);
    }

    @PostMapping("/api/v1/scripts/generate")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> generateScript(@RequestBody Map<String,Object> body) {
        requireTopic(body);
        String topic = String.valueOf(body.get("topic"));
        String language = String.valueOf(body.getOrDefault("language", "en"));
        String format = String.valueOf(body.getOrDefault("format", "short"));
        String tone = String.valueOf(body.getOrDefault("tone", "clear and engaging"));
        String audience = String.valueOf(body.getOrDefault("audience", "Beginners"));
        String generated = ai.generate(topic, language, format, tone, audience);
        Map<String,Object> result = new LinkedHashMap<>(body);
        result.put("full_text", generated);
        result.put("generation_mode", "openai");
        return records.create("script", "script_draft", result);
    }

    @PostMapping("/api/v1/seo/generate")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> generateSeo(@RequestBody Map<String,Object> body) {
        requireTopic(body);
        String topic = String.valueOf(body.get("topic")).trim();
        List<String> tags = Arrays.stream(topic.toLowerCase(Locale.ROOT).split("[^a-z0-9]+"))
                .filter(word -> word.length() > 2).distinct().limit(8).toList();
        Map<String,Object> result = new LinkedHashMap<>(body);
        result.put("suggested_title", topic + " explained simply");
        result.put("description", "Learn the basics of " + topic + " in this beginner-friendly video. Subscribe for more practical technology explainers.");
        result.put("tags", tags);
        result.put("hashtags", tags.stream().limit(3).map(tag -> "#" + tag).toList());
        result.put("generation_mode", "template_fallback");
        result.put("provider_message", "Starter SEO metadata. AI keyword research and live search-volume data are not connected yet.");
        return records.create("seo", "seo_draft", result);
    }

    @PostMapping("/api/v1/voice/generate")
    public Map<String,Object> generateVoice(@RequestBody Map<String,Object> body) {
        throw new ResponseStatusException(HttpStatus.NOT_IMPLEMENTED,
                "Voice generation is not migrated to the Java backend yet. No audio was generated.");
    }

    @PostMapping("/api/v1/render/title-card")
    public Map<String,Object> renderTitleCard(@RequestBody Map<String,Object> body) {
        throw new ResponseStatusException(HttpStatus.NOT_IMPLEMENTED,
                "FFmpeg rendering is not migrated to the Java backend yet. No video was rendered.");
    }

    @PostMapping("/api/v1/videos")
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String,Object> video(@RequestBody Map<String,Object> body) {
        if (body.get("title") == null || String.valueOf(body.get("title")).isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Video title is required.");
        }
        body.putIfAbsent("thumbnail_url", null);
        return records.create("video", "video_review", body);
    }

    @PostMapping("/api/v1/videos/{id}/approve")
    public Map<String,Object> approve(@PathVariable String id, @RequestBody(required = false) Map<String,Object> body) {
        var video = records.get(id);
        ensureVideo(video);
        Map<String,Object> patch = new HashMap<>();
        patch.put("approval_note", body == null ? "" : body.getOrDefault("note", ""));
        patch.put("approved_at", Instant.now().toString());
        return records.change(id, "approved", patch);
    }

    @PostMapping("/api/v1/videos/{id}/reject")
    public Map<String,Object> reject(@PathVariable String id, @RequestBody(required = false) Map<String,Object> body) {
        var video = records.get(id);
        ensureVideo(video);
        Map<String,Object> patch = Map.of("review_note", body == null ? "" : body.getOrDefault("note", ""));
        return records.change(id, "changes_requested", patch);
    }

    @PostMapping("/api/v1/publishing/{id}/schedule")
    public Map<String,Object> schedule(@PathVariable String id, @RequestBody Map<String,Object> body) {
        var video = records.get(id);
        ensureVideo(video);
        if (!"approved".equals(video.get("status"))) {
            throw new ResponseStatusException(HttpStatus.CONFLICT,
                    "Publishing blocked: approve the final video and metadata first.");
        }
        throw new ResponseStatusException(HttpStatus.NOT_IMPLEMENTED,
                "Java YouTube OAuth upload integration is the next migration stage. No video was published.");
    }

    @GetMapping("/api/v1/analytics/overview")
    public Map<String,Object> analytics() {
        var all = records.list(null);
        var videos = all.stream().filter(x -> "video".equals(x.get("kind"))).toList();
        return Map.of(
                "ideas", all.stream().filter(x -> "idea".equals(x.get("kind"))).count(),
                "scripts", all.stream().filter(x -> "script".equals(x.get("kind"))).count(),
                "videos", videos.size(),
                "awaiting_review", videos.stream().filter(x -> "video_review".equals(x.get("status"))).count(),
                "approved", videos.stream().filter(x -> "approved".equals(x.get("status"))).count(),
                "scheduled", videos.stream().filter(x -> "scheduled".equals(x.get("status"))).count(),
                "published", videos.stream().filter(x -> "published".equals(x.get("status"))).count(),
                "views", 0, "watch_time_hours", 0,
                "note", "Connect YouTube Analytics OAuth to load real channel performance.");
    }

    private void requireTopic(Map<String,Object> body) {
        Object topic = body.get("topic");
        if (topic == null || String.valueOf(topic).trim().length() < 3) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Topic must contain at least 3 characters.");
        }
    }

    private void ensureVideo(Map<String,Object> item) {
        if (!"video".equals(item.get("kind"))) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Only video records support this action.");
        }
    }
}