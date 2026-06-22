import { Link, NavLink, Navigate, Route, Routes } from "react-router-dom";
import Graph from "./routes/Graph.jsx";
import Lexicon from "./routes/Lexicon.jsx";
import Usage from "./routes/Usage.jsx";

export default function App() {
  return (
    <>
      <nav className="nav">
        <Link to="/usage" className="brand" title="사용법으로">
          research-atlas
        </Link>
        <NavLink to="/usage">사용법</NavLink>
        <NavLink to="/graph">지형도</NavLink>
        <NavLink to="/lexicon">사전</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/usage" replace />} />
        <Route path="/usage" element={<Usage />} />
        <Route path="/graph" element={<Graph />} />
        <Route path="/lexicon" element={<Lexicon />} />
      </Routes>
    </>
  );
}
