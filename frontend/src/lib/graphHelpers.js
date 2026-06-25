// 지형도 화면(Graph)·렌더러가 공유하는 상수·순수 유틸. React 무관.

export const TYPE_COLOR = {
  technique: "#2563eb",
  benchmark: "#d97706",
  analysis: "#7c3aed",
  survey: "#059669",
  other: "#888",
};

// 대화 이력 localStorage 복원(chatWidth 패턴). 파싱 실패 시 빈 배열.
// key별로 분리: "chatMessages"=명령 탭 / "collectMessages"=수집 탭.
export function loadMessages(key) {
  try {
    const raw = localStorage.getItem(key);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

// arXiv ID "2502.14192" → 등장 연월 "2025-02". 형식이 다르면 null.
export function arxivMonth(id) {
  const m = String(id).slice(0, 4);
  if (!/^\d{4}$/.test(m)) return null;
  return `20${m.slice(0, 2)}-${m.slice(2, 4)}`;
}

// 노드 등장 시점 = papers 중 가장 이른 연월. papers 없으면 null(시점 불명).
export function nodeMonth(node) {
  if (!node.papers || node.papers.length === 0) return null;
  let earliest = null;
  for (const id of node.papers) {
    const ym = arxivMonth(id);
    if (ym && (!earliest || ym < earliest)) earliest = ym;
  }
  return earliest;
}

// 채팅 폭 제약: min 300px(카드 가독성) ~ max min(창폭*0.55, 720)(그래프 안 사라지게)
export const CHAT_MIN = 300;
export function clampChat(w) {
  const max = Math.min(window.innerWidth * 0.55, 720);
  return Math.max(CHAT_MIN, Math.min(w, max));
}
