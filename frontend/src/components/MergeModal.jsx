import { useState } from "react";

// 병합 모달 — window.prompt 대체. 대상 개념을 검색해 클릭하면 병합.
export default function MergeModal({ from, items, onCancel, onConfirm }) {
  const [q, setQ] = useState("");
  const ql = q.trim().toLowerCase();
  const candidates = items
    .filter((it) => it.name !== from)
    .filter((it) => !ql || it.name.toLowerCase().includes(ql))
    .slice(0, 50);

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>
          <b>{from}</b> 을(를) 다른 개념의 alias로 병합
        </h3>
        <p className="muted">
          대상 개념을 고르면 <b>{from}</b> 이(가) 그 개념의 alias로 흡수되고 삭제됩니다.
        </p>
        <input
          autoFocus
          className="modal-search"
          placeholder="대상 개념 검색…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="modal-list">
          {candidates.length === 0 ? (
            <div className="muted" style={{ padding: 10 }}>
              일치하는 개념 없음
            </div>
          ) : (
            candidates.map((it) => (
              <button
                key={it.name}
                className="modal-item"
                onClick={() => onConfirm(it.name)}
              >
                <span>{it.name}</span>
                <span className={`badge st-${it.status}`}>{it.status}</span>
              </button>
            ))
          )}
        </div>
        <div className="modal-actions">
          <button onClick={onCancel}>취소</button>
        </div>
      </div>
    </div>
  );
}
