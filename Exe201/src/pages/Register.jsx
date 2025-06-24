import { useState } from "react";
import { Link, useNavigate } from "react-router-dom"; // Thêm useNavigate
import logo from "../assets/logov1.webp";
import { handleregister } from "../Context/Auth"; // Import handleregister
import "../css/Register.css";

const Register = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [repeatPassword, setRepeatPassword] = useState("");
  const [agreeTOS, setAgreeTOS] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!agreeTOS) {
      setError("You must agree to the Terms of Service");
      return;
    }
    if (password !== repeatPassword) {
      setError("Passwords do not match");
      return;
    }
    const result = await handleregister(email, password, setError);
    if (result.success) {
      alert(result.message);
      navigate("/"); // Điều hướng về trang login
    } else {
      alert(error);
    }
  };

  return (
    <div className="regi_page">
      <img src={logo} alt="..." className="regi_logo" />
      <h2>Create Account</h2>
      <form className="regi_form" onSubmit={onSubmit}>
        <input
          className="input_regi"
          placeholder="Your Name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="input_regi"
          placeholder="Your Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="input_regi"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <input
          className="input_regi"
          placeholder="Repeat your password"
          type="password"
          value={repeatPassword}
          onChange={(e) => setRepeatPassword(e.target.value)}
          required
        />
        <div className="TOS_agree">
          <input
            type="checkbox"
            checked={agreeTOS}
            onChange={(e) => setAgreeTOS(e.target.checked)}
          />
          I agree all statements in Terms of service
        </div>
        {error && <p className="error">{error}</p>} {/* Hiển thị lỗi nếu có */}
        <button className="sign_btn" type="submit">
          SIGN UP
        </button>
        <div>
          Already have an account?
          <Link className="go_to_log" to="/">
            Login here
          </Link>
        </div>
      </form>
    </div>
  );
};

export default Register;
