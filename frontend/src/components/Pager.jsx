// 페이저 — 사전 목록 상·하단 재사용.
export default function Pager({ page, pageCount, pageSize, total, onPage }) {
  return (
    <div className="lex-pager">
      <span className="muted">
        {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} / {total}
      </span>
      {pageCount > 1 && (
        <span className="lex-pager-ctrl">
          <button disabled={page <= 1} onClick={() => onPage(page - 1)}>
            ‹ 이전
          </button>
          <span className="muted">
            {page} / {pageCount}
          </span>
          <button disabled={page >= pageCount} onClick={() => onPage(page + 1)}>
            다음 ›
          </button>
        </span>
      )}
    </div>
  );
}
