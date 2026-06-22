// 모든 호출은 상대경로 → Vite proxy가 :8000으로 전달.
async function jsonOrThrow(res) {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${body}`);
  }
  return res.json();
}

export const getGraph = (withPapers = false) =>
  fetch(`/api/graph?papers=${withPapers ? "true" : "false"}`).then(jsonOrThrow);

export const getLexicon = () => fetch("/api/lexicon").then(jsonOrThrow);

export const patchLexicon = (name, patch) =>
  fetch(`/api/lexicon/${encodeURIComponent(name)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  }).then(jsonOrThrow);

export const mergeLexicon = (from, into) =>
  fetch("/api/lexicon/merge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from, into }),
  }).then(jsonOrThrow);

export const rebuild = () =>
  fetch("/api/rebuild", { method: "POST" }).then(jsonOrThrow);

// 검토 도우미 제안(정적 스냅샷). 적용은 patchLexicon/mergeLexicon 재사용.
export const getReviewSuggestions = () =>
  fetch("/api/review_suggestions").then(jsonOrThrow);

// 개념 '검토함' 토글 → reviewed.json 기록
export const postReviewed = (id, reviewed) =>
  fetch("/api/concept/reviewed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, reviewed }),
  }).then(jsonOrThrow);

export const postCommand = (text) =>
  fetch("/api/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }).then(jsonOrThrow);

// --- 수집 에이전트 (LangGraph 흐름) ---
export const collectStart = (text) =>
  fetch("/api/collect/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }).then(jsonOrThrow);

// signal: AbortController.signal (추출 단계 타임아웃용, 선택)
export const collectResume = (thread_id, decision, signal) =>
  fetch("/api/collect/resume", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id, decision }),
    signal,
  }).then(jsonOrThrow);

// 새로고침/재접속 시 thread_id로 현재 수집 상태 복원. 없으면 404.
export const collectGetState = (thread_id) =>
  fetch(`/api/collect/state?thread_id=${encodeURIComponent(thread_id)}`).then(
    jsonOrThrow
  );
