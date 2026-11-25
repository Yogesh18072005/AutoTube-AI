package ai.autotube.records;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ContentRecordRepository extends JpaRepository<ContentRecord, String> {
    List<ContentRecord> findAllByOrderByCreatedAtDesc();
    List<ContentRecord> findByKindOrderByCreatedAtDesc(String kind);
}