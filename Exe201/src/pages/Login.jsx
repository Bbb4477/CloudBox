import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import logo from "../assets/logov1.webp";
import { handlelogin } from "../Context/Auth";
import "../css/Login.css";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onSubmit = async (e) => {
    e.preventDefault();
    const result = await handlelogin(email, password, setError);
    if (result.success) {
      alert(result.message);
      navigate("/home");
    } else {
      alert(error);
    }
  };

  return (
    <div className="login_page">
      <img src={logo} alt="..." className="login_logo" />
      <h2>Welcome to CloudBox</h2>
      <form className="login_form" onSubmit={onSubmit}>
        {" "}
        <div>
          <h5>Username or Email Address</h5>
          <input
            className="input_log"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <h5>Password</h5>
          <input
            className="input_log"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="error">{error}</p>}
        <div className="regis_n_log_btn">
          <Link to="/register" className="regis_button">
            Don't have an account?
          </Link>
          <button className="login_button" type="submit">
            Log in
          </button>
        </div>
      </form>
    </div>
  );
};

export default Login;
