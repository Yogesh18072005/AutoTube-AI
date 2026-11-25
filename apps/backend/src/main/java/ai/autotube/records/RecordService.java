package ai.autotube.records;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import java.util.*;

@Service
public class RecordService {
    private final ContentRecordRepository repository;
    private final ObjectMapper mapper;

    public RecordService(ContentRecordRepository repository, ObjectMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    public List<Map<String, Object>> list(String kind) {
        var rows = (kind == null || kind.isBlank())
                ? repository.findAllByOrderByCreatedAtDesc()
                : repository.findByKindOrderByCreatedAtDesc(kind);
        return rows.stream().map(this::toMap).toList();
    }

    public Map<String, Object> get(String id) {
        return repository.findById(id).map(this::toMap)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Record not found"));
    }

    public Map<String, Object> create(String kind, String status, Map<String, Object> data) {
        try {
            return toMap(repository.save(new ContentRecord(kind, status, mapper.writeValueAsString(data))));
        } catch (JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid record data");
        }
    }

    public Map<String, Object> change(String id, String status, Map<String, Object> patch) {
        var row = repository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Record not found"));
        try {
            Map<String, Object> data = mapper.readValue(row.getData(), Map.class);
            if (patch != null) data.putAll(patch);
            row.update(status, mapper.writeValueAsString(data));
            return toMap(repository.save(row));
        } catch (JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Could not update record");
        }
    }

    private Map<String, Object> toMap(ContentRecord row) {
        try {
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("id", row.getId());
            result.put("kind", row.getKind());
            result.put("status", row.getStatus());
            result.put("data", mapper.readValue(row.getData(), Map.class));
            result.put("created_at", row.getCreatedAt().toString());
            result.put("updated_at", row.getUpdatedAt().toString());
            return result;
        } catch (JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Stored record is invalid");
        }
    }
}