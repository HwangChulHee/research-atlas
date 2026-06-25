// 사전(Lexicon) 화면 공유 상수·헬퍼.

// 제안 action 문자열 → (action, target). "merge_into:DPR" → ["merge","DPR"].
export function parseAction(s) {
  if (s && s.startsWith("merge_into:")) return ["merge", s.slice(11)];
  return [s, null];
}

// 한글 표기(표시용 — 내부 로직은 원문 사용)
export const CAT_KR = {
  lineage: "계보",
  component: "부품",
  generic: "일반어",
  substrate: "베이스모델",
  author_year: "저자-연도 인용",
  umbrella: "우산범주",
  duplicate: "중복",
};

export function actionKr([act, tgt]) {
  if (act === "approve") return "승인";
  if (act === "reject") return "거부";
  if (act === "merge") return `병합 → ${tgt || "?"}`;
  return act;
}

export const STATUSES = ["approved", "unreviewed", "pending", "rejected"];
export const FILTERS = ["pending", "unreviewed", "approved", "rejected", "all"];
export const PAGE_SIZES = [10, 20, 40];

// 각 상태가 뭘 의미하는지 — 그래프 표시 여부 포함(NODE_OK = approved/unreviewed).
export const STATUS_INFO = [
  ["approved", "승인됨 · 그래프 표시"],
  ["unreviewed", "논문이 정의 · 그래프 표시 · 검토 전"],
  ["pending", "참조로만 등장 · 그래프 미표시 · 검토 대기"],
  ["rejected", "거부됨 · 그래프 미표시"],
];

// 제안 확신도 정렬 키(low→med→high).
export const CONF = { low: 0, med: 1, high: 2 };
