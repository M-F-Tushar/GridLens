# GridLens — Technical & Operational Limitations

> **Knowledge Base Source:** System limitations ingested into the RAG knowledge base reside at [`data/knowledge/system_limitations.md`](../data/knowledge/system_limitations.md). Comprehensive audit details are available in [`docs/gridlens_comprehensive_audit_report.md`](gridlens_comprehensive_audit_report.md).

---

## 1. Electrical & Physical Simplifications

- **No AC Power Flow:** GridLens performs deterministic hourly algebraic energy accounting (kWh). It does not compute bus voltages, reactive power (kVAR), power factor, AC frequency, transformer saturation, or transmission line thermal impedance.
- **Asymmetric Battery Efficiency:** Round-trip efficiency ($\eta$) is applied as $\sqrt{\eta}$ exclusively during the charging phase; discharge calculations apply zero loss to internal state of charge. While conservation of net energy holds over complete cycles, discharging appears lossless at instantaneous time-steps.
- **No Degradation Dynamics:** Battery cycling, depth of discharge (DoD) degradation, temperature effects, and C-rate limits are not modeled.

## 2. Simulation & Data Boundaries

- **Single Pre-configured Site:** Out of the box, the engine supports `campus-microgrid-a`. Additional sites require corresponding hourly fixture profiles.
- **14-Day Cyclic Boundary:** Default fixtures contain 336 hours of continuous data. Horizons extending beyond 336 hours wrap modulo the fixture length.
- **Synthetic Data:** Bundled demand, solar, and carbon profiles are synthetic and educational; they should not be used as the sole basis for real-world capital investment decisions.

## 3. RAG Retrieval & State Persistence

- **Hash-Based Embeddings:** Zero-dependency 256-bucket hash embeddings generate non-zero similarity for random word overlaps (typically 0.10–0.28). A similarity threshold of `0.30` is enforced by default to prevent false-positive answers on off-topic questions.
- **Ephemeral In-Memory State:** Vector store chunks, similarity caches, and conversational sessions (`SessionRegistry`) live in process memory. Restarting the server resets all in-memory histories.
