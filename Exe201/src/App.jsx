import { Route, Routes, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import "./css/App.css";
import ContainerDetail from "./pages/ContainerDetail";
import Dashboard from "./pages/Dashboard";
import Home from "./pages/Home";
import Install from "./pages/Install";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Scaling from "./pages/Scaling";

function App() {
  const location = useLocation();
  return (
    <div>
      {location.pathname !== "/" && location.pathname !== "/register" && (
        <Sidebar />
      )}
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/home" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/scaling" element={<Scaling />} />
        <Route path="/container/:id/:service" element={<ContainerDetail />} />
        <Route path="/install" element={<Install />} />
      </Routes>
    </div>
  );
}

export default App;
