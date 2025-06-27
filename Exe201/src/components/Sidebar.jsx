import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import logo from "../assets/logov1.webp";
import "../css/Sidebar.css";
import LogoutModal from "./LogoutModal";

const Sidebar = ({ isExpanded, setIsExpanded }) => {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const username = sessionStorage.getItem("userName");
    if (username) {
      setUserEmail(username);
    }
  }, []);

  const toggleSidebar = () => {
    setIsExpanded(!isExpanded);
  };

  const handleLogoutClick = () => {
    setIsModalOpen(true);
  };

  const confirmLogout = () => {
    sessionStorage.removeItem("userName");
    setUserEmail(null);
    navigate("/");
    setIsModalOpen(false);
  };

  const cancelLogout = () => {
    setIsModalOpen(false);
  };

  return (
    <div className={`sidebar ${isExpanded ? "expanded" : "collapsed"}`}>
      <button className="toggle-button" onClick={toggleSidebar}>
        {isExpanded ? "☰" : "☰"}
      </button>

      <div className="logo-container">
        <span className="logo">
          <img src={logo} alt="Cloudbox Logo" className="sidebar-logo" />
        </span>
      </div>

      <ul>
        <li className="user-info">
          <span className="icon">👤</span>
          <span className="text">{userEmail}</span>
        </li>
        <li>
          <NavLink to="/home">
            <span className="icon">🏠</span>
            <span className="text">Dashboard</span>
          </NavLink>
        </li>
        <li className="logout">
          <button onClick={handleLogoutClick}>
            <span className="icon">🚪</span>
            <span className="text">Logout</span>
          </button>
        </li>
      </ul>
      <LogoutModal
        isOpen={isModalOpen}
        onConfirm={confirmLogout}
        onCancel={cancelLogout}
      />
    </div>
  );
};

export default Sidebar;
