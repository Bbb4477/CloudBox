import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  deleteService,
  handleAgentList,
  handleBoxList,
  startService,
  stopService,
} from "../Context/Controller";
import BackupModal from "../components/BackupModal";
import Loading from "../components/Loading";
import "../css/Home.css";

const Home = () => {
  const { agentId } = useParams();
  const [data, setData] = useState([]);
  const [agentData, setAgentData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [openConfigMenuId, setOpenConfigMenuId] = useState(null);
  const [isBackupModalOpen, setIsBackupModalOpen] = useState(false);
  const [selectedContainerId, setSelectedContainerId] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAgentData = async () => {
      const result = await handleAgentList(setError);
      if (result.success) {
        const agentMap = result.data.reduce((acc, agent) => {
          acc[agent.id] = agent.description || agent.id;
          return acc;
        }, {});
        setAgentData(agentMap);
      }
    };
    fetchAgentData();
  }, []);

  const onSendPayload = async () => {
    setLoading(true);
    setError("");
    setSuccessMessage("");
    const result = await handleBoxList(agentId, setError);
    if (result.success) {
      setData(result.data);
    }
    setLoading(false);
  };

  useEffect(() => {
    onSendPayload();
  }, [agentId]);

  const handleToggleStatus = async (containerId, currentStatus) => {
    try {
      setError("");
      setSuccessMessage("");
      setLoading(true);
      let result;
      if (currentStatus === "running") {
        result = await stopService(agentId, containerId);
      } else if (currentStatus === "stopped") {
        result = await startService(agentId, containerId);
      } else {
        setError("Cannot toggle status for this service.");
        setLoading(false);
        return;
      }

      setLoading(false);
      if (!result.success) {
        setError(result.error || "Error toggling service status");
        return;
      }

      setSuccessMessage(result.message);
      const updatedData = data.map((container) =>
        container.containerId === containerId
          ? {
              ...container,
              status: currentStatus === "running" ? "stopped" : "running",
            }
          : container
      );
      setData(updatedData);

      setTimeout(() => setSuccessMessage(""), 600000);
    } catch (err) {
      setLoading(false);
      setError("Error toggling service status");
      console.error("Toggle Status Error:", err);
    }
  };

  const handleDeleteService = async (containerId, serviceName) => {
    if (!window.confirm(`Are you sure you want to delete ${serviceName}?`)) {
      return;
    }

    try {
      setError("");
      setSuccessMessage("");
      setLoading(true);
      const result = await deleteService(agentId, containerId);
      setLoading(false);

      if (!result.success) {
        setError(result.error || "Error deleting service");
        return;
      }

      setSuccessMessage(result.message);
      const updatedData = data.filter(
        (container) => container.containerId !== containerId
      );
      setData(updatedData);

      setTimeout(() => setSuccessMessage(""), 600000);
    } catch (err) {
      setLoading(false);
      setError("Error deleting service");
      console.error("Delete Service Error:", err);
    } finally {
      setOpenConfigMenuId(null);
    }
  };

  const toggleConfigMenu = (containerId) => {
    setOpenConfigMenuId(openConfigMenuId === containerId ? null : containerId);
  };

  const openBackupModal = (containerId) => {
    setSelectedContainerId(containerId);
    setOpenConfigMenuId(null); // Close the config menu when opening the modal
    setIsBackupModalOpen(true);
  };

  const closeBackupModal = () => {
    setIsBackupModalOpen(false);
    setSelectedContainerId(null);
  };

  const transformedData = data.map((container) => {
    const containerId = container.containerId;
    const serviceName = container.service;
    const agentName = agentData[agentId] || "Unknown Agent";
    const status =
      typeof container.status === "object"
        ? container.status.status || "unknown"
        : container.status;
    return {
      ID: containerId,
      Name: agentName,
      ServiceName: serviceName,
      Status: status,
      FullContainer: container,
    };
  });

  return (
    <div className="home_content">
      <h3>Services for {agentData[agentId] || agentId}</h3>
      <button className="send" onClick={onSendPayload} disabled={loading}>
        {loading ? "Refreshing..." : "Refresh"}
      </button>
      {loading && <Loading />}
      {error && <p className="error">{error}</p>}
      {successMessage && (
        <p className="success-message" aria-live="polite">
          {successMessage}
        </p>
      )}
      <div className="container_list">
        {transformedData.length > 0
          ? transformedData.map((container, index) => (
              <div className="container_box" key={index}>
                <div className="container-block">
                  <div
                    onClick={() =>
                      navigate(
                        `/container/${container.ID}/${container.ServiceName}`,
                        {
                          state: {
                            container: container.FullContainer,
                            serviceName: container.ServiceName,
                            agentId: agentId,
                          },
                        }
                      )
                    }
                    style={{ cursor: "pointer" }}
                  >
                    <p className="service_name">{container.ServiceName}</p>
                  </div>
                  <div className="actions">
                    <div
                      className={`toggle-switch ${container.Status} ${
                        container.Status !== "running" &&
                        container.Status !== "stopped"
                          ? "disabled"
                          : ""
                      }`}
                      onClick={() =>
                        container.Status === "running" ||
                        container.Status === "stopped"
                          ? handleToggleStatus(container.ID, container.Status)
                          : null
                      }
                      tabIndex={0}
                      role="switch"
                      aria-checked={container.Status === "running"}
                    >
                      <div className="thumb"></div>
                      <span>
                        {container.Status === "running" ? "Running" : "Stopped"}
                      </span>
                    </div>
                    <div className="config-container">
                      <button
                        className="config-button"
                        onClick={() => toggleConfigMenu(container.ID)}
                        aria-label={`Configure ${container.ServiceName}`}
                        aria-expanded={openConfigMenuId === container.ID}
                        aria-controls={`config-menu-${container.ID}`}
                        tabIndex={0}
                      >
                        ⚙️
                      </button>
                      {openConfigMenuId === container.ID && (
                        <div
                          className="config-menu"
                          id={`config-menu-${container.ID}`}
                        >
                          <button
                            className="delete-option"
                            onClick={() =>
                              handleDeleteService(
                                container.ID,
                                container.ServiceName
                              )
                            }
                            aria-label={`Delete ${container.ServiceName}`}
                            tabIndex={0}
                          >
                            Delete
                          </button>
                          <button
                            className="backup-option"
                            onClick={() => openBackupModal(container.ID)}
                            aria-label={`View backups for ${container.ServiceName}`}
                            tabIndex={0}
                          >
                            Back up
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          : !loading && <p>No services available</p>}
      </div>
      <BackupModal
        isOpen={isBackupModalOpen}
        onClose={closeBackupModal}
        agentId={agentId}
        containerId={selectedContainerId}
      />
    </div>
  );
};

export default Home;
