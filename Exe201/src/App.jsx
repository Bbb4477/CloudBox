import { useState, useEffect } from "react";
import { Route, Routes, useLocation, useNavigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import "./css/App.css";
import ContainerDetail from "./pages/ContainerDetail";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Install from "./pages/Install";
import Login from "./pages/Login";

function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);

  const isLoginOrRegister = location.pathname === "/";

  useEffect(() => {
    const userName = sessionStorage.getItem("userName");
    const protectedRoutes = [
      "/home",
      "/agent/:agentId/services",
      "/install/:agentId",
      "/container/:containerId/:service",
    ];
    if (
      !userName &&
      protectedRoutes.some((route) =>
        location.pathname.startsWith(route.split(":")[0])
      )
    ) {
      navigate("/");
    }
  }, [location.pathname, navigate]);

  return (
    <div
      className={`app-container ${
        isSidebarExpanded ? "sidebar-expanded" : "sidebar-collapsed"
      } ${isLoginOrRegister ? "no-grid" : ""}`}
    >
      {location.pathname !== "/" && (
        <Sidebar
          isExpanded={isSidebarExpanded}
          setIsExpanded={setIsSidebarExpanded}
        />
      )}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/home" element={<Dashboard />} />
          <Route path="/agent/:agentId/services" element={<Home />} />
          <Route path="/install/:agentId" element={<Install />} />
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
