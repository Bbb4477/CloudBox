import axios from "axios";

const API_BASE =
  "https://9368-14-226-226-52.ngrok-free.app/joQitzSI4jenCsIbJ1cLfw4uDgIBeayztKer41HH4jr1QDTXQYivOqcqYAk3I3c7";
const OVERVIEW_ENDPOINT = "/agent/overview";
const AGENT_LIST_ENDPOINT = "/agent/list";
const SERVICE_LIST_ENDPOINT = "/server/availableService";
const CREATE_AGENT_ENDPOINT = "/agent/create";
const REMOVE_AGENT_ENDPOINT = "/agent/remove";
const DELETE_SERVICE_ENDPOINT = "/agent/box/delete";
const BACK_UP_LIST_ENDPOINT = "/agent/box/backup/list";
const SAVE_BACK_UP_ENDPOINT = "/agent/box/backup";
const REMOVE_BACK_UP_ENDPOINT = "/agent/box/backup/remove";
const RESTORE_BACK_UP_ENDPOINT = "/agent/box/restore";

export const handleRestoreBackup = async (
  agentID,
  boxID,
  backupID,
  backupType,
  setError
) => {
  try {
    console.log("Sending restore request:", {
      agentID,
      boxID,
      backupID,
      backupType,
    });
    const payload = { agentID, boxID, backupID, backupType };
    const response = await axios.post(
      `${API_BASE}${RESTORE_BACK_UP_ENDPOINT}`,
      payload,
      { timeout: 10000 } // Thêm timeout để tránh treo
    );
    console.log("Restore response:", response.data);

    return {
      success: true,
      message: `Successfully restored ${boxID} with backup ${backupID} on agent ${agentID}`,
      data: response.data,
    };
  } catch (err) {
    console.error(
      "Restore Backup Error:",
      err.message,
      err.response?.data,
      err.code
    );
    setError(`Error restoring backup ${backupID}: ${err.message}`);
    return {
      success: false,
      data: err.response?.data || {},
      error: err.message,
    };
  }
};

export const handleRemoveBackup = async (
  agentID,
  boxID,
  backupID,
  setError
) => {
  try {
    const payload = { agentID, boxID, backupID };
    const response = await axios.post(
      `${API_BASE}${REMOVE_BACK_UP_ENDPOINT}`,
      payload
    );

    return {
      success: true,
      message: `Successfully removed backup ${backupID} for ${boxID} on agent ${agentID}`,
      data: response.data,
    };
  } catch (err) {
    console.error("Remove Backup Error:", err.message, err.response?.data);
    setError(`Error removing backup ${backupID}: ${err.message}`);
    return { success: false };
  }
};

export const handlePostbackup = async (agentID, boxID, setError) => {
  try {
    const payload = { agentID, boxID, backupType: "data" }; // Thêm backupType theo API
    const response = await axios.post(
      `${API_BASE}${SAVE_BACK_UP_ENDPOINT}`,
      payload
    );

    return {
      success: true,
      message: `Successfully saved ${boxID} on agent ${agentID}`,
      data: response.data,
    };
  } catch (err) {
    console.error("Save Error:", err.message, err.response?.data);
    setError(`Error saving ${boxID}: ${err.message}`);
    return { success: false };
  }
};

export const handleBackupList = async (agentID, boxID, setError) => {
  try {
    const payload = { agentID, boxID }; // Required payload
    const response = await axios.post(
      `${API_BASE}${BACK_UP_LIST_ENDPOINT}`,
      payload
    );
    let data = response.data;

    console.log("Raw Backup List Response:", {
      status: response.status,
      data: typeof data === "string" ? data.substring(0, 200) : data,
      headers: response.headers,
    });

    if (typeof data === "string") {
      if (data.trim().startsWith("<")) {
        console.error("Received HTML response:", data.substring(0, 200));
        setError("Server returned an error page instead of JSON data");
        return { success: false, data: [] };
      }
      try {
        data = JSON.parse(data);
      } catch (parseError) {
        console.error("Failed to parse backup list:", parseError);
        setError("Invalid data format from server");
        return { success: false, data: [] };
      }
    }

    // Handle the data (assume array or object of backups)
    let backups = data;
    if (typeof backups === "object" && !Array.isArray(backups)) {
      backups = Object.keys(backups).map((key) => ({
        id: key,
        name: backups[key] || key,
      }));
    } else if (Array.isArray(backups)) {
      backups = backups.map((item, index) => ({
        id: index,
        name: typeof item === "string" ? item : JSON.stringify(item),
      }));
    } else {
      backups = [];
    }

    console.log("Parsed Backup List Response:", backups);
    return {
      success: true,
      message: "Backup list fetched successfully!",
      data: backups,
    };
  } catch (err) {
    console.error("Backup List Error:", err.message, err.response?.data);
    setError(`Error fetching backup list: ${err.message}`);
    return { success: false, data: [] };
  }
};

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

export const handleBoxList = async (agentID, setError) => {
  const payload = {
    agentID: agentID,
  };

  try {
    const response = await axios.post(
      `${API_BASE}${OVERVIEW_ENDPOINT}`,
      payload
    );
    let data = response.data;

    if (typeof data === "string") {
      try {
        data = JSON.parse(data.replace(/(\w+):/g, '"$1":'));
      } catch (parseError) {
        console.error("Failed to parse API response:", parseError);
        setError("Invalid data format from server");
        return { success: false };
      }
    }

    // Chuyển object thành mảng các service
    if (typeof data === "object" && !Array.isArray(data)) {
      data = Object.entries(data).map(([containerId, status]) => ({
        containerId,
        service: containerId.split("_").pop().toLowerCase(),
        status,
      }));
    } else if (!Array.isArray(data)) {
      data = [];
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

export const handleInstall = async (agentID, service, setError) => {
  try {
    const payload = { agentID, service };
    const response = await axios.post(`${API_BASE}/agent/box/install`, payload);
    return {
      success: true,
      message: `Successfully installed ${service} on agent ${agentID}`,
      data: response.data,
    };
  } catch (err) {
    console.error("Install Error:", err.message, err.response?.data);
    setError(`Error installing ${service}: ${err.message}`);
    return { success: false };
  }
};

// Hàm mới để lấy chi tiết container
export const handleContainerDetail = async (
  agentId,
  containerId,
  setError,
  useContainerId = false
) => {
  const payload = useContainerId
    ? { containerID: containerId }
    : { agentID: agentId };

  try {
    const response = await axios.post(
      `${API_BASE}${OVERVIEW_ENDPOINT}`,
      payload
    );
    let data = response.data;
    console.log("Raw API Response:", data); // Debug

    // Kiểm tra lỗi
    if (typeof data === "string") {
      if (
        data.includes("Invalid AgentID") ||
        data.includes("Invalid ContainerID")
      ) {
        setError(
          useContainerId
            ? "Invalid ContainerID provided"
            : "Invalid AgentID provided"
        );
        return { success: false, data: null };
      }
      if (data.trim().startsWith("<")) {
        setError("Server returned an error page instead of JSON data");
        return { success: false, data: null };
      }
      try {
        data = JSON.parse(data.replace(/(\w+):/g, '"$1":'));
      } catch (parseError) {
        console.error("Failed to parse API response:", parseError);
        setError("Invalid data format from server");
        return { success: false, data: null };
      }
    }

    // Nếu dùng containerId, giả định API trả về chi tiết container trực tiếp
    if (useContainerId) {
      if (typeof data === "object" && data.containerId) {
        return {
          success: true,
          message: "Container details fetched successfully!",
          data: {
            containerId: data.containerId,
            service:
              data.containerId?.split("_").pop()?.toLowerCase() || "unknown",
            status: data.status,
          },
        };
      }
      setError("Container not found");
      return { success: false, data: null };
    }

    // Nếu dùng agentId, chuyển object thành mảng container
    if (typeof data === "object" && !Array.isArray(data)) {
      data = Object.entries(data).map(([id, status]) => ({
        containerId: id,
        service: id.split("_").pop().toLowerCase(),
        status,
      }));
    } else if (!Array.isArray(data)) {
      data = [];
    }

    // Tìm container khớp với containerId
    const matchedContainer = data.find((c) => c.containerId === containerId);
    if (!matchedContainer) {
      setError("Container not found");
      return { success: false, data: null };
    }

    console.log("Container Detail Response:", matchedContainer);
    return {
      success: true,
      message: "Container details fetched successfully!",
      data: matchedContainer,
    };
  } catch (err) {
    console.error("Container Detail Error:", err.message, err.response?.data);
    setError(`Error fetching container details: ${err.message}`);
    return { success: false, data: null };
  }
};

export const startService = async (agentID, boxID) => {
  try {
    const payload = { agentID, boxID };
    const response = await axios.post(`${API_BASE}/agent/box/start`, payload);
    let message = response.data;

    console.log("Raw Start Service Response:", {
      status: response.status,
      data: message.substring(0, 200),
      headers: response.headers,
    });

    if (typeof message !== "string") {
      console.error("Unexpected response format:", message);
      return {
        success: false,
        error: "Unexpected response format from server",
      };
    }

    if (message.trim().startsWith("<")) {
      console.error("Received HTML response:", message.substring(0, 200));
      return {
        success: false,
        error: "Server returned an error page instead of expected data",
      };
    }

    message = message.trim(); // Remove trailing \n

    console.log("Parsed Start Service Response:", message);
    return {
      success: true,
      message,
      data: response.data,
    };
  } catch (err) {
    console.error("Start Service Error:", {
      message: err.message,
      response: err.response?.data,
      status: err.response?.status,
    });
    return {
      success: false,
      error: err.response?.data || `Error starting service: ${err.message}`,
    };
  }
};

// Hàm sửa: Dừng dịch vụ
export const stopService = async (agentID, boxID) => {
  try {
    const payload = { agentID, boxID };
    const response = await axios.post(`${API_BASE}/agent/box/stop`, payload);
    let message = response.data;

    console.log("Raw Stop Service Response:", {
      status: response.status,
      data: message.substring(0, 200),
      headers: response.headers,
    });

    if (typeof message !== "string") {
      console.error("Unexpected response format:", message);
      return {
        success: false,
        error: "Unexpected response format from server",
      };
    }

    if (message.trim().startsWith("<")) {
      console.error("Received HTML response:", message.substring(0, 200));
      return {
        success: false,
        error: "Server returned an error page instead of expected data",
      };
    }

    message = message.trim(); // Remove trailing \n

    console.log("Parsed Stop Service Response:", message);
    return {
      success: true,
      message,
      data: response.data,
    };
  } catch (err) {
    console.error("Stop Service Error:", {
      message: err.message,
      response: err.response?.data,
      status: err.response?.status,
    });
    return {
      success: false,
      error: err.response?.data || `Error stopping service: ${err.message}`,
    };
  }
};

export const handleCreateAgent = async (formData, setError) => {
  try {
    const response = await axios.post(
      `${API_BASE}${CREATE_AGENT_ENDPOINT}`,
      formData
    );
    let data = response.data;

    console.log("Raw Create Agent Response:", {
      status: response.status,
      data: typeof data === "string" ? data.substring(0, 200) : data,
      headers: response.headers,
    });

    if (typeof data === "string") {
      if (data.trim().startsWith("<")) {
        console.error("Received HTML response:", data.substring(0, 200));
        setError("Server returned an error page instead of JSON data");
        return { success: false };
      }
      try {
        data = JSON.parse(data);
      } catch (parseError) {
        console.error("Failed to parse create agent response:", parseError);
        setError("Invalid data format from server");
        return { success: false };
      }
    }

    if (response.status === 200 && data.agentID && data.message) {
      const { agentID, downloadUrl, message } = data;
      console.log("Parsed Create Agent Response:", {
        agentID,
        downloadUrl,
        message,
      });
      return { success: true, agentID, downloadUrl, message };
    } else {
      setError(data.message || "Failed to create agent");
      return { success: false };
    }
  } catch (error) {
    console.error("Create Agent Error:", {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
    });
    setError(error.response?.data?.message || "Error creating agent");
    return { success: false };
  }
};

export const handleRemoveAgent = async (agentID, setError) => {
  try {
    const response = await axios.post(`${API_BASE}${REMOVE_AGENT_ENDPOINT}`, {
      agentID,
    });
    let data = response.data;

    console.log("Raw Remove Agent Response:", {
      status: response.status,
      data: typeof data === "string" ? data.substring(0, 200) : data,
      headers: response.headers,
    });

    if (typeof data === "string") {
      if (data.trim().startsWith("<")) {
        console.error("Received HTML response:", data.substring(0, 200));
        setError("Server returned an error page instead of JSON data");
        return { success: false };
      }
      try {
        data = JSON.parse(data);
      } catch (parseError) {
        console.error("Failed to parse remove agent response:", parseError);
        setError("Invalid data format from server");
        return { success: false };
      }
    }

    if (response.status === 200) {
      console.log("Parsed Remove Agent Response:", data);
      return {
        success: true,
        message: data.message || `Agent ${agentID} removed successfully`,
      };
    } else {
      setError(data.message || "Failed to remove agent");
      return { success: false };
    }
  } catch (error) {
    console.error("Remove Agent Error:", {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
    });
    setError(error.response?.data?.message || "Error removing agent");
    return { success: false };
  }
};

export const deleteService = async (agentID, boxID) => {
  try {
    const payload = { agentID, boxID };
    const response = await axios.post(
      `${API_BASE}${DELETE_SERVICE_ENDPOINT}`,
      payload
    );
    let message = response.data;

    console.log("Raw Delete Service Response:", {
      status: response.status,
      data: message.substring(0, 200),
      headers: response.headers,
    });

    if (typeof message !== "string") {
      console.error("Unexpected response format:", message);
      return {
        success: false,
        error: "Unexpected response format from server",
      };
    }

    if (message.trim().startsWith("<")) {
      console.error("Received HTML response:", message.substring(0, 200));
      return {
        success: false,
        error: "Server returned an error page instead of expected data",
      };
    }

    message = message.trim(); // Remove trailing \n

    console.log("Parsed Delete Service Response:", message);
    return {
      success: true,
      message,
      data: response.data,
    };
  } catch (err) {
    console.error("Delete Service Error:", {
      message: err.message,
      response: err.response?.data,
      status: err.response?.status,
    });
    return {
      success: false,
      error: err.response?.data || `Error deleting service: ${err.message}`,
    };
  }
};
