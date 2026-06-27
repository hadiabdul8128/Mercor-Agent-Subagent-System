# AutoQC Criteria

The nine AutoQC categories, their subcriteria, and what each future specialist subagent will
inspect. One specialist subagent per category (Phase 3). Specialists **diagnose and propose
only** — they never apply patches.

---

## 1. Solution Integrity

Ensures the task's solution is sound and the world contains no out-of-world leakage.

**Subcriteria**
- **Out-of-World Residue in Document Body and Metadata** — generator comments, prompt text,
  tool names, or meta-annotations leaking into documents or metadata.
- **Content Leakage** — answer/solution content visible where it should not be.
- **Golden Answer Traceability** — the golden answer is actually recoverable from the world files.
- **World Spec Alignment** — documents match the world specification.
- **Trap Survival Through File Generation** — intended traps still exist after generation.

**Specialist will inspect:** document bodies and metadata for residue/leakage, traceability of
the golden answer to source documents, alignment to the world spec, and survival of intended
traps through the generation pipeline.

---

## 2. Clinical Accuracy

Ensures clinical content is numerically and medically plausible.

**Subcriteria**
- **Calculation and Fixture Accuracy** — derived values and fixtures compute correctly.
- **Clinical Values Plausible** — labs, vitals, dosages fall in plausible ranges.
- **Clinical Code Validity** — ICD/CPT/LOINC/RxNorm-style codes are valid and correctly used.

**Specialist will inspect:** arithmetic in derived fields, plausibility of clinical values, and
validity of clinical codes. Defers to human review for genuine clinical judgment.

---

## 3. Medication Reconciliation

Ensures medications are consistent and correctly attributed.

**Subcriteria**
- **Prescriber Attribution Integrity** — each medication is attributed to a valid, consistent
  prescriber.
- **Medication List Consistency** — medication lists agree across documents (names, doses,
  routes, frequencies).

**Specialist will inspect:** prescriber attribution across documents and internal/cross-document
medication list agreement.

---

## 4. Cross-Document Consistency

Ensures shared fields agree across all documents.

**Subcriteria**
- **Cross-Document Field Consistency** — shared fields (names, DOB, MRN, dates, demographics)
  match across every document.

**Specialist will inspect:** every shared field across the document set for agreement — while
respecting intentional inconsistencies that belong to a trap.

---

## 5. Temporal Integrity

Ensures chronology is coherent and properly anchored.

**Subcriteria**
- **Document Chronology and Sequencing** — events and documents occur in a sensible order.
- **Task Temporal Anchoring Verified** — the task is anchored to the correct point in time.
- **World Files Dated No Later Than July 2025** — no world file is dated after July 2025.

**Specialist will inspect:** event ordering, the task's temporal anchor, and the July-2025 date
ceiling — without flattening intentional timing-based traps.

---

## 6. Trap Architecture

Ensures deliberate traps are present, resolvable, and documented.

**Subcriteria**
- **Traps Logically Resolvable** — each trap can be resolved from available evidence.
- **Trap Documentation and Density** — traps are documented and present at the intended density.

**Specialist will inspect:** logical resolvability of each trap and trap documentation/density.
**Never** removes or weakens a trap — that is an escalation, not a fix.

---

## 7. Completeness

Ensures the required file set and supporting data are present.

**Subcriteria**
- **File Set Complete** — all required files exist.
- **Supporting Clinical Data Present** — supporting data needed for the task is included.

**Specialist will inspect:** presence of all required files and supporting clinical data.

---

## 8. Realism and Authenticity

Ensures documents read as authentic clinical writing, not AI-generated text.

**Subcriteria**
- **Realism & Authenticity: Clinical Cold-Read + AI Tells** — a cold read passes as genuine
  clinical documentation, with no AI "tells" (over-hedging, templated phrasing, uniformity).

**Specialist will inspect:** clinical register, naturalness, and AI tells on a cold read —
without normalizing intentional irregularities that add realism or serve a trap.

---

## 9. Documentation Standards

Ensures formatting, register, length, and completeness meet standards.

**Subcriteria**
- **Documentation Standards: Formatting, Register & Length** — formatting, clinical register, and
  length conform to standards.
- **Content Completeness (No Gaps)** — no missing required sections or content gaps.

**Specialist will inspect:** formatting/register/length conformance and absence of content gaps.

---

## Routing note

Before any specialist acts, the Intake/Classifier Agent determines **folder scope**
(`filesystem/`, `tasks/`, `.meta/`, `unknown`). A category match does **not** by itself authorize
a world-file edit — scope governs whether a writer fix is even appropriate. See
`docs/PROJECT_CONTEXT.md`.
