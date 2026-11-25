package ai.autotube;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class AutoTubeApplicationTests {
    @Autowired MockMvc mvc;

    @Test
    void healthEndpointWorks() throws Exception {
        mvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.service").value("autotube-java-api"));
    }

    @Test
    void workspaceSettingsCanBeSavedAndLoaded() throws Exception {
        mvc.perform(put("/api/v1/settings")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"channel_name\":\"Test Channel\",\"default_language\":\"hi\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.channel_name").value("Test Channel"))
                .andExpect(jsonPath("$.default_language").value("hi"));

        mvc.perform(get("/api/v1/settings"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.channel_name").value("Test Channel"));
    }

    @Test
    void ideaCanBeCreatedAndListed() throws Exception {
        mvc.perform(post("/api/v1/ideas")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"topic\":\"A test idea about Java APIs\",\"language\":\"en\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.kind").value("idea"));
    }

    @Test
    void publishingIsBlockedUntilVideoIsApproved() throws Exception {
        String response = mvc.perform(post("/api/v1/videos")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\":\"Java test video\",\"language\":\"en\",\"format\":\"short\"}"))
                .andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        String id = com.fasterxml.jackson.databind.json.JsonMapper.builder().build()
                .readTree(response).get("id").asText();

        mvc.perform(post("/api/v1/publishing/" + id + "/schedule")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"scheduled_at\":\"2026-12-01T12:00:00Z\"}"))
                .andExpect(status().isConflict());

        mvc.perform(post("/api/v1/videos/" + id + "/approve")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"note\":\"Reviewed\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("approved"));

        mvc.perform(post("/api/v1/publishing/" + id + "/schedule")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"scheduled_at\":\"2026-12-01T12:00:00Z\"}"))
                .andExpect(status().isNotImplemented());
    }
}
