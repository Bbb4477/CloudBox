import drupalIcon from "../assets/drupal.png";
import filebrowserIcon from "../assets/filebrowser.png";
import wordpressIcon from "../assets/wordpress.png";

export const ICONS = {
  wordpress: wordpressIcon,
  filebrowser: filebrowserIcon,
  drupal: drupalIcon,
};

export const getIconByService = (serviceName) => {
  if (typeof serviceName !== "string") {
    console.warn("Invalid service name:", serviceName);
    return null; // Fallback for non-string inputs
  }
  return ICONS[serviceName.toLowerCase()] || null;
};
