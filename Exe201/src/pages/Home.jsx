import { useEffect, useState } from "react"; // Thêm useEffect để fetch agent data
import { useNavigate } from "react-router-dom";
import { handleAgentList, handleBoxList } from "../Context/Controller";
import { getIconByService } from "../Context/ImageController";
import "../css/Home.css";

const Home = () => {
  const [error, setError] = useState("");
  const [containerData, setContainerData] = useState([]);
  const [agentData, setAgentData] = useState({}); // Lưu trữ dữ liệu agent
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Fetch agent data when component mounts
  useEffect(() => {
    const fetchAgentData = async () => {
      const result = await handleAgentList(setError);
      if (result.success) {
        const agentMap = result.data.reduce((acc, agent) => {
          acc[agent.id] = agent.description || agent.id; // Giả định agent có field 'description'
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
    const result = await handleBoxList(setError);
    setLoading(false);

    if (result.success) {
      try {
        let data = result.data;
        if (!Array.isArray(data)) {
          data = [data];
        }
        const transformedData = data.map((container) => {
          const containerId = Object.keys(container)[0];
          const serviceData = container[containerId];
          const serviceName = containerId.split("_").pop().toLowerCase();
          // Giả định agentID là "agent01" (có thể cần điều chỉnh dựa trên API)
          const agentName = agentData["agent01"] || "Unknown Agent"; // Lấy tên agent
          return {
            ID: containerId,
            Name: agentName, // Sử dụng tên agent thay vì containerId
            [serviceName]: serviceData,
          };
        });
        setContainerData(transformedData);
      } catch (parseError) {
        setError("Failed to process container data");
        console.error("Parse Error:", parseError);
        setContainerData([]);
      }
    }
  };

  const handleServiceClick = (container, serviceName) => {
    navigate(`/container/${container.ID}/${serviceName}`, {
      state: { container, serviceName },
    });
  };

  const getServiceIcon = (serviceName) => {
    const lowerServiceName = serviceName.toLowerCase();
    if (lowerServiceName.includes("wordpress"))
      return getIconByService("wordpress");
    if (lowerServiceName.includes("filebrowser"))
      return getIconByService("filebrowser");
    return null;
  };

  return (
    <div className="home_page">
      <div className="home_content">
        <h3>Home</h3>
        <button className="send" onClick={onSendPayload} disabled={loading}>
          {loading ? "Sending..." : "Send Payload"}
        </button>
        {error && <p className="error">{error}</p>}
        {containerData.length > 0
          ? containerData.map((container, index) => (
              <div className="container_box" key={index}>
                <button
                  className="installation"
                  onClick={() => navigate("/scaling")}
                >
                  +
                </button>
                <div className="container-block">
                  <h4>{container.Name}</h4> {/* Hiển thị tên agent */}
                  {Object.entries(container)
                    .filter(([key]) => key !== "ID" && key !== "Name")
                    .map(([serviceName, serviceData], idx) => (
                      <div
                        key={idx}
                        className="service-block"
                        onClick={() =>
                          handleServiceClick(container, serviceName)
                        }
                      >
                        {getServiceIcon(serviceName) ? (
                          <img
                            src={getServiceIcon(serviceName)}
                            alt={serviceName}
                            className="service-icon"
                          />
                        ) : (
                          <span className="service-icon">📦</span>
                        )}
                        <span>{serviceName}</span>
                      </div>
                    ))}
                </div>
              </div>
            ))
          : !loading && <p>No data available</p>}
      </div>
    </div>
  );
};

export default Home;
