import { useEffect, useState } from "react";
import { handleAgentList } from "../Context/Controller";
import "../css/Dashboard.css";

const Dashboard = () => {
  const [error, setError] = useState("");
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAgents = async () => {
      setLoading(true);
      setError("");
      const result = await handleAgentList(setError);
      setLoading(false);

      if (result.success) {
        setAgents(result.data);
      }
    };

    fetchAgents();
  }, []);

  return (
    <div className="dashboard_page">
      <div className="dashboard_content">
        <h3>Dashboard - Agents</h3>
        {loading && <p>Loading agents...</p>}
        {error && <p className="error">{error}</p>}
        {agents.length > 0
          ? agents.map((agent, index) => (
              <div key={index} className="agent-block">
                <span className="agent-icon">👤</span>
                <span>{agent.description || "No description"}</span>
                <span>Status: {agent.status}</span>
              </div>
            ))
          : !loading && !error && <p>No agents available</p>}
      </div>
    </div>
  );
};

export default Dashboard;
