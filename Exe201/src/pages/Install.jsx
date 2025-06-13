import { useEffect, useState } from "react";
import { handleServiceList } from "../Context/Controller";
import { getIconByService } from "../Context/ImageController";
import "../css/Install.css";

const Install = () => {
  const [error, setError] = useState("");
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchServices = async () => {
      setLoading(true);
      setError("");
      const result = await handleServiceList(setError);
      setLoading(false);

      if (result.success) {
        const mappedServices = result.data.map((service) => ({
          id: service.id || service, // Fallback to service if id is missing
          name: service.name || service, // Fallback to service if name is missing
        }));
        setServices(mappedServices);
      }
    };

    fetchServices();
  }, []);

  return (
    <div className="scaling_page">
      <div className="scaling_content">
        <h3>Scaling - Available Services</h3>
        {loading && <p>Loading services...</p>}
        {error && <p className="error">{error}</p>}
        {services.length > 0
          ? services.map((service, index) => (
              <div key={index} className="service-block">
                {getIconByService(service.name) ? (
                  <img
                    src={getIconByService(service.name)}
                    alt={service.name}
                    className="service-icon"
                  />
                ) : (
                  <span className="service-icon">📦</span> // Fallback icon
                )}
                <span>{service.name}</span>
              </div>
            ))
          : !loading && !error && <p>No services available</p>}
      </div>
    </div>
  );
};

export default Install;
