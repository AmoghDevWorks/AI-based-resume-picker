Phase 1 → Build candidates + score (skill, experience, platform)
Phase 2 → Assemble DataFrame (without TF-IDF yet)
Phase 3 → HoneypotFilter removes bad profiles          ← NEW
Phase 4 → Filter resume_texts to surviving IDs only    ← NEW
Phase 5 → TF-IDF runs on the smaller clean set         ← FIXED
Phase 6 → Aggregate → rank → notice bonus → rank → min-score filter