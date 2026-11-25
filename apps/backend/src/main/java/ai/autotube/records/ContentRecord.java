package ai.autotube.records;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "content_records", indexes = {
        @Index(name = "idx_content_kind_status", columnList = "kind,status"),
        @Index(name = "idx_content_created", columnList = "createdAt")
})
public class ContentRecord {
    @Id
    private String id;
    @Column(nullable = false, length = 40)
    private String kind;
    @Column(nullable = false, length = 40)
    private String status;
    @Column(nullable = false, columnDefinition = "text")
    private String data;
    @Column(nullable = false)
    private Instant createdAt;
    @Column(nullable = false)
    private Instant updatedAt;

    protected ContentRecord() {}

    public ContentRecord(String kind, String status, String data) {
        this.id = UUID.randomUUID().toString();
        this.kind = kind;
        this.status = status;
        this.data = data;
        this.createdAt = Instant.now();
        this.updatedAt = this.createdAt;
    }

    public void update(String status, String data) {
        if (status != null) this.status = status;
        if (data != null) this.data = data;
        this.updatedAt = Instant.now();
    }

    public String getId() { return id; }
    public String getKind() { return kind; }
    public String getStatus() { return status; }
    public String getData() { return data; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
}