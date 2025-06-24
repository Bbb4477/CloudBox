import { useState } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import "./css/App.css";
import ContainerDetail from "./pages/ContainerDetail";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Install from "./pages/Install";
import Login from "./pages/Login";
import Register from "./pages/Register";

function App() {
  const location = useLocation();
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);

  const isLoginOrRegister =
    location.pathname === "/" || location.pathname === "/register";

  return (
    <div
      className={`app-container ${
        isSidebarExpanded ? "sidebar-expanded" : "sidebar-collapsed"
      } ${isLoginOrRegister ? "no-grid" : ""}`}
    >
      {location.pathname !== "/" && location.pathname !== "/register" && (
        <Sidebar
          isExpanded={isSidebarExpanded}
          setIsExpanded={setIsSidebarExpanded}
        />
      )}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/home" element={<Dashboard />} />{" "}
          <Route path="/agent/:agentId/services" element={<Home />} />{" "}
          <Route path="/install/:agentId" element={<Install />} />{" "}
          <Route
            path="/container/:containerId/:service"
            element={<ContainerDetail />}
          />
        </Routes>
      </main>
    </div>
  );
}

export default App;
