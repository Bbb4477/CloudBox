import axios from "axios";

const API = "https://67c7faf7c19eb8753e7bae06.mockapi.io/api/huy/users";

export const handlelogin = async (email, password, setError) => {
  try {
    const response = await axios.get(API);
    const users = response.data;
    console.log("API Response:", users);
    const user = users.find(
      (u) => u.email === email && u.password === password
    );
    if (user) {
      sessionStorage.setItem("userEmail", email);
      return { success: true, message: "Login successful!" };
    } else {
      setError("Invalid username or password");
      return { success: false };
    }
  } catch (err) {
    console.error("API Error:", err.message, err.response);
    setError("Error connecting to the server");
    return { success: false };
  }
};

export const handleregister = async (email, password, setError) => {
  try {
    const response = await axios.post(API, { email, password });
    if (response.status === 201) {
      return {
        success: true,
        message: "Registration successful! Please login.",
      };
    } else {
      setError("Registration failed");
      return { success: false };
    }
  } catch (err) {
    console.error("API Error:", err.message, err.response);
    setError("Error connecting to the server");
    return { success: false };
  }
};
