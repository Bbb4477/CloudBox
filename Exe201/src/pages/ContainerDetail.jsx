import { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import { handleContainerDetail } from "../Context/Controller";
import "../css/ContainerDetail.css";

const ContainerDetail = () => {
  const { containerId, service } = useParams();
  const { state } = useLocation();
  const [container, setContainer] = useState(state?.container || null);
  const [error, setError] = useState("");
  const [reset, setReset] = useState(false); // Kept but unused; clarify if needed

  const agentId = state?.agentId; // Get agentId from state

  useEffect(() => {
    if (!agentId) {
      setError("Missing agent ID");
      return;
    }

    const fetchContainerDetails = async () => {
      const result = await handleContainerDetail(
        agentId,
        containerId,
        setError,
        false
      );
      if (result.success) {
        setContainer(result.data);
      } else if (result.success === false) {
        setError(result.error || "Failed to fetch container details");
      }
    };

    fetchContainerDetails(); // Initial fetch
    const intervalId = setInterval(fetchContainerDetails, 2000); // Refresh every 2 seconds

    return () => clearInterval(intervalId); // Cleanup
  }, [agentId, containerId]); // Depend on agentId and containerId

  if (!container || !service || error) {
    return (
      <div className="container-detail">
        <p>{error || `No data available for ${service || containerId}`}</p>
      </div>
    );
  }

  const status =
    typeof container.status === "object"
      ? container.status.status || "unknown"
      : container.status;
  const stats = container.status?.stats
    ? Object.entries(container.status.stats)
    : [];

  return (
    <div className="container-detail">
      <h3>Container Details - {service}</h3>
      <div className="detail-section">
        <h4>
          <strong>Container ID:</strong> {container.containerId}
        </h4>
        <br />
        {status === "running" && stats.length > 0 ? (
          stats.map(([key, stat], index) => (
            <div className="stats-section" key={index}>
              <h4>Container Stats - {stat.Name}</h4>
              <p>
                <strong>Name:</strong> {stat.Name}
              </p>
              <p>
                <strong>Container ID:</strong> {stat.Container}
              </p>
              <p>
                <strong>CPU Usage:</strong> {stat.CPUPerc}
              </p>
              <p>
                <strong>Memory Usage:</strong> {stat.MemUsage} ({stat.MemPerc})
              </p>
              <p>
                <strong>Network I/O:</strong> {stat.NetIO}
              </p>
              <p>
                <strong>Block I/O:</strong> {stat.BlockIO}
              </p>
              <p>
                <strong>PIDs:</strong> {stat.PIDs}
              </p>
              <br />
            </div>
          ))
        ) : (
          <p>No stats available (Container is {status})</p>
        )}
      </div>
    </div>
  );
};

export default ContainerDetail;
