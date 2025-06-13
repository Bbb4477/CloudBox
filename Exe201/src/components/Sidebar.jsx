import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import "../css/Sidebar.css";

const Sidebar = () => {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState(null);

  useEffect(() => {
    const email = sessionStorage.getItem("userEmail");
    if (email) {
      setUserEmail(email);
    }
  }, []);

  const handleLogout = () => {
    sessionStorage.removeItem("userEmail");
    setUserEmail(null);
    navigate("/");
  };

  return (
    <div className="sidebar">
      <ul>
        <div>
          <li className="sidebar_logo">
            <NavLink to="/home">
              <img src={logo} alt="Logo" />
            </NavLink>
          </li>
          <li>
            <span className="user-icon">👤</span>
            <span className="user-email">{userEmail}</span>
          </li>
          <li>
            <NavLink to="/dashboard">Dashboard</NavLink>
          </li>
          <li>
            <NavLink to="/scaling">Scaling</NavLink>
          </li>
          <li>
            <NavLink to="/orchestrate">Orchestrate</NavLink>
          </li>
        </div>
        <div className="lgout">
          <li>
            <button onClick={handleLogout}>Logout</button>
          </li>
        </div>
      </ul>
    </div>
  );
};

export default Sidebar;
