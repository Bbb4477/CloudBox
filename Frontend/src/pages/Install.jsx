import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  handleAgentList,
  handleInstall,
  handleServiceList,
} from "../Context/Controller";
import { getIconByService } from "../Context/ImageController";
import "../css/Install.css";

const Install = () => {
  const { agentId } = useParams();
  const [services, setServices] = useState([]);
  const [agentName, setAgentName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [installMessage, setInstallMessage] = useState("");

  useEffect(() => {
    const fetchAgentData = async () => {
      const result = await handleAgentList(setError);
      if (result.success) {
        const agent = result.data.find((a) => a.id === agentId);
        setAgentName(agent ? agent.description || agent.id : "Unknown Agent");
      }
    };
    fetchAgentData();
  }, [agentId]);

  useEffect(() => {
    const fetchServices = async () => {
      setLoading(true);
      const result = await handleServiceList(setError);
      if (result.success) {
        console.log("Services:", result.data); // Log to verify service names
        setServices(result.data);
      }
      setLoading(false);
    };
    fetchServices();
  }, []);

  const handleInstallClick = async (serviceName) => {
    setInstallMessage("");
    const result = await handleInstall(agentId, serviceName, setError);
    if (result.success) {
      setInstallMessage(result.data);
    }
  };

  return (
    <div className="install_content">
      <h3>InstallStore on {agentName}</h3>
      {loading && <p>Loading...</p>}
      {error && <p>{error}</p>}
      {installMessage && <p>{installMessage}</p>}
      {services.length > 0 ? (
        <div className="service-container">
          {services.map((service, index) => (
            <div key={index} className="service-wrapper">
              <div className="service-block">
                {getIconByService(service.name) ? (
                  <img
                    src={getIconByService(service.name)}
                    alt={service.name}
                    className="service-icon"
                  />
                ) : (
                  <span className="service-icon">📦</span>
                )}
              </div>
              <div className="service-block1">
                <p className="service-name">{service.name}</p>
              </div>
              <button
                className="install-btn"
                onClick={() => handleInstallClick(service.name)}
              >
                Install
              </button>
            </div>
          ))}
        </div>
      ) : (
        !loading && <p>No available services</p>
      )}
    </div>
  );
};

export default Install;
