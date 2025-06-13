import axios from "axios";

const API_BASE =
  "https://4a0b-14-226-226-52.ngrok-free.app/joQitzSI4jenCsIbJ1cLfw4uDgIBeayztKer41HH4jr1QDTXQYivOqcqYAk3I3c7";
const OVERVIEW_ENDPOINT = "/agent/overview";
const AGENT_LIST_ENDPOINT = "/agent/list";
const SERVICE_LIST_ENDPOINT = "/server/availableService";

export const handleServiceList = async (setError) => {
  try {
    const response = await axios.post(
      `${API_BASE}${SERVICE_LIST_ENDPOINT}`,
      {}
    );
    let data = response.data;
    if (typeof data === "string") {
      try {
        data = JSON.parse(data);
      } catch (parseError) {
        console.error("Failed to parse service list:", parseError);
        setError("Invalid data format from server");
        return { success: false };
      }
    }

    if (!Array.isArray(data)) {
      data =
        Object.keys(data).length > 0
          ? Object.keys(data).map((key) => ({ id: key, name: data[key] }))
          : [];
    } else {
      // Handle array of strings from API
      data = data.map((service) => ({ id: service, name: service })); // Ensure name is set
    }

    console.log("Service List Response:", data); // Verify the structure
    return {
      success: true,
      message: "Service list fetched successfully!",
      data: data,
    };
  } catch (err) {
    console.error("Service List Error:", err.message, err.response);
    setError("Error connecting to the server for service list");
    return { success: false };
  }
};

export const handleBoxList = async (setError) => {
  const payload = {
    agentID: "agent01",
  };

  try {
    const response = await axios.post(
      `${API_BASE}${OVERVIEW_ENDPOINT}`,
      payload
    );
    let data = response.data;

    if (typeof data === "string") {
      try {
        data = data.replace(/(\w+):/g, '"$1":');
        data = JSON.parse(data);
      } catch (parseError) {
        console.error("Failed to parse API response:", parseError);
        setError("Invalid data format from server");
        return { success: false };
      }
    }

    if (!Array.isArray(data)) {
      data = [data];
    }

    console.log("Parsed API_BOX Response:", data);
    return {
      success: true,
      message: "Box list request successful!",
      data: data,
    };
  } catch (err) {
    console.error("API_BOX Error:", err.message, err.response);
    setError("Error connecting to the box list server");
    return { success: false };
  }
};

export const handleAgentList = async (setError) => {
  try {
    const response = await axios.post(`${API_BASE}${AGENT_LIST_ENDPOINT}`, {});
    let data = response.data;

    console.log("Raw Agent List Response:", {
      status: response.status,
      data: data.substring(0, 200),
      headers: response.headers,
    });

    if (typeof data === "string" && data.trim().startsWith("<")) {
      console.error(
        "Received HTML response instead of JSON:",
        data.substring(0, 200)
      );
      setError(
        `Server returned an error page instead of JSON data. Status: ${response.status}`
      );
      return { success: false, data: [] };
    }

    if (typeof data === "string") {
      try {
        data = JSON.parse(data);
      } catch (parseError) {
        console.error("Failed to parse agent list:", parseError);
        setError("Invalid data format from server");
        return { success: false };
      }
    }

    if (typeof data === "object" && !Array.isArray(data)) {
      data = Object.keys(data).map((agentId) => ({
        id: agentId,
        ...data[agentId],
      }));
    } else if (!Array.isArray(data)) {
      data = [];
    }

    console.log("Agent List Response:", data);
    return {
      success: true,
      message: "Agent list fetched successfully!",
      data: data,
    };
  } catch (err) {
    console.error(
      "Agent List Error:",
      err.message,
      err.response?.data || err.response?.statusText,
      err.response?.headers
    );
    setError(
      `Error connecting to the server for agent list: ${err.message} (Status: ${err.response?.status})`
    );
    return { success: false };
  }
};
