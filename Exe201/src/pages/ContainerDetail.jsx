import { useLocation, useParams } from "react-router-dom";
import "../css/ContainerDetail.css";

const ContainerDetail = () => {
  const { state } = useLocation();
  const { id, service } = useParams(); // Extract id and service from the URL
  const container = state?.container;

  // Find the specific service data
  const serviceData = container ? container[service] : null;

  return (
    <div className="container-detail">
      <h3>Container Details - {service}</h3>
      {container && serviceData ? (
        <pre>{JSON.stringify({ [service]: serviceData }, null, 2)}</pre>
      ) : (
        <p>No data available for {service}</p>
      )}
    </div>
  );
};

export default ContainerDetail;
