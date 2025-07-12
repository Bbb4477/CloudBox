import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  handleAgentList,
  handleCreateAgent,
  handleRemoveAgent,
} from "../Context/Controller";
import Loading from "../components/Loading";
import "../css/Dashboard.css";

const Dashboard = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [successModalOpen, setSuccessModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedAgentID, setSelectedAgentID] = useState("");
  const [configMenuOpen, setConfigMenuOpen] = useState(null); // Tracks which agent's config menu is open
  const [formData, setFormData] = useState({
    description: "",
    host: "",
    ports: "",
    sharehost: "",
  });
  const [successResponse, setSuccessResponse] = useState({
    agentID: "",
    downloadUrl: "",
    message: "",
  });
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAgents = async () => {
      setLoading(true);
      const result = await handleAgentList(setError);
      if (result.success) {
        setAgents(result.data);
      }
      setLoading(false);
    };
    fetchAgents();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.description || !formData.host || !formData.ports) {
      setError("Description, host, and ports are required.");
      return;
    }
    setModalOpen(false);
    setLoading(true);
    const result = await handleCreateAgent(formData, setError);
    setLoading(false);
    if (result.success) {
      setSuccessResponse({
        agentID: result.agentID || "Unknown",
        downloadUrl: result.downloadUrl || "",
        message: result.message || "Agent created successfully",
      });
      setSuccessModalOpen(true);
      setFormData({ description: "", host: "", ports: "", sharehost: "" });
      const agentResult = await handleAgentList(setError);
      if (agentResult.success) {
        setAgents(agentResult.data);
      }
    }
  };

  const handleCloseSuccessModal = () => {
    setSuccessModalOpen(false);
    setSuccessResponse({ agentID: "", downloadUrl: "", message: "" });
    setError("");
  };

  const handleOpenDeleteModal = (agentID) => {
    setSelectedAgentID(agentID);
    setConfigMenuOpen(null);
    setDeleteModalOpen(true);
  };

  const handleDeleteAgent = async () => {
    setDeleteModalOpen(false);
    setLoading(true);
    const result = await handleRemoveAgent(selectedAgentID, setError);
    setLoading(false);
    if (result.success) {
      setSuccessResponse({
        agentID: selectedAgentID,
        downloadUrl: "",
        message:
          result.message || `Agent ${selectedAgentID} removed successfully`,
      });
      setSuccessModalOpen(true);
      const agentResult = await handleAgentList(setError);
      if (agentResult.success) {
        setAgents(agentResult.data);
      }
    }
    setSelectedAgentID("");
  };

  const toggleConfigMenu = (agentID) => {
    setConfigMenuOpen(configMenuOpen === agentID ? null : agentID);
  };

  return (
    <div className="dashboard_content">
      <div className="dashboard_header">
        <h3>Agent List</h3>
        <button
          className="create-agent-button"
          onClick={() => setModalOpen(true)}
        >
          Create Agent
        </button>
      </div>
      {loading && <Loading />}
      {error && !loading && <p className="error">{error}</p>}
      {agents.length > 0
        ? agents.map((agent, index) => (
            <div key={index} className="agent-block">
              <button
                className="install-button"
                onClick={() => navigate(`/install/${agent.id}`)}
              >
                +
              </button>
              <div
                className="agent-info"
                onClick={() => navigate(`/agent/${agent.id}/services`)}
                tabIndex={0}
                role="button"
                onKeyDown={(e) =>
                  (e.key === "Enter" || e.key === " ") &&
                  navigate(`/agent/${agent.id}/services`)
                }
              >
                <span className="agent-icon">👤</span>
                <span>{agent.description || "No description"}</span>
                <span>Status: {agent.status}</span>
              </div>
              <div className="config-container">
                <button
                  className="config-button"
                  onClick={() => toggleConfigMenu(agent.id)}
                  tabIndex={0}
                  onKeyDown={(e) =>
                    (e.key === "Enter" || e.key === " ") &&
                    toggleConfigMenu(agent.id)
                  }
                >
                  ⚙️
                </button>
                {configMenuOpen === agent.id && (
                  <div className="config-menu">
                    <button
                      className="delete-option"
                      onClick={() => handleOpenDeleteModal(agent.id)}
                      tabIndex={0}
                      onKeyDown={(e) =>
                        (e.key === "Enter" || e.key === " ") &&
                        handleOpenDeleteModal(agent.id)
                      }
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        : !loading && !error && <p>No agents available</p>}
      {modalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h4>Create New Agent</h4>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <input
                  type="text"
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="host">Host (e.g., 192.168.32.133:5000)</label>
                <input
                  type="text"
                  id="host"
                  name="host"
                  value={formData.host}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="ports">Ports (e.g., 10000-10020)</label>
                <input
                  type="text"
                  id="ports"
                  name="ports"
                  value={formData.ports}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="sharehost">Share Host (optional)</label>
                <input
                  type="text"
                  id="sharehost"
                  name="sharehost"
                  value={formData.sharehost}
                  onChange={handleInputChange}
                />
              </div>
              <div className="modal-actions">
                <button type="submit">Create</button>
                <button type="button" onClick={() => setModalOpen(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {successModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h4>
              {successResponse.downloadUrl
                ? "Agent Creation Successful"
                : "Agent Deletion Successful"}
            </h4>
            <div className="success-message">
              <p>{successResponse.message}</p>
              <p>Agent ID: {successResponse.agentID}</p>
              {successResponse.downloadUrl && (
                <a href={successResponse.downloadUrl} download>
                  <button className="install-agent-button">Install</button>
                </a>
              )}
            </div>
            <div className="modal-actions">
              <button onClick={handleCloseSuccessModal}>Next</button>
              <button onClick={handleCloseSuccessModal}>Cancel</button>
            </div>
          </div>
        </div>
      )}
      {deleteModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h4>Confirm Deletion</h4>
            <p>Are you sure you want to delete Agent {selectedAgentID}?</p>
            <div className="modal-actions">
              <button
                className="confirm-delete-button"
                onClick={handleDeleteAgent}
                tabIndex={0}
                onKeyDown={(e) =>
                  (e.key === "Enter" || e.key === " ") && handleDeleteAgent()
                }
              >
                Yes
              </button>
              <button
                onClick={() => {
                  setDeleteModalOpen(false);
                  setSelectedAgentID("");
                }}
                tabIndex={0}
                onKeyDown={(e) =>
                  (e.key === "Enter" || e.key === " ") &&
                  setDeleteModalOpen(false) &&
                  setSelectedAgentID("")
                }
              >
                No
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
