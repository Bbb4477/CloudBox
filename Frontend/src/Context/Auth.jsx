import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const API_KEY = import.meta.env.VITE_API_KEY;
const API_BASE = `${API_BASE_URL}/${API_KEY}`;

const LOG_END_POINT = "login";

export const handlelogin = async (username, password, setError) => {
  try {
    const response = await axios.post(`${API_BASE}/${LOG_END_POINT}`, {
      username,
      password,
    });
    const result = response.data;
    console.log("API Response:", result);

    if (result === "success") {
      sessionStorage.setItem("userName", username);
      return {
        success: true,
        message: "Login successful!",
        redirectTo: "/home",
      };
    } else if (result === "fail") {
      setError("Invalid username or password");
      return { message: "Login fail!", success: false };
    } else {
      setError("Unexpected response from server");
      return { success: false };
    }
  } catch (err) {
    console.error("API Error:", err.message, err.response);
    setError("Error connecting to the server");
    return { success: false };
  }
};

// export const handleregister = async (email, password, setError) => {
//   try {
//     const response = await axios.post(API, { email, password });
//     if (response.status === 201) {
//       return {
//         success: true,
//         message: "Registration successful! Please login.",
//       };
//     } else {
//       setError("Registration failed");
//       return { success: false };
//     }
//   } catch (err) {
//     console.error("API Error:", err.message, err.response);
//     setError("Error connecting to the server");
//     return { success: false };
//   }
// };
