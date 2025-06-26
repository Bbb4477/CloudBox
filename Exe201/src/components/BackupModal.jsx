import { useEffect, useState } from "react";
import {
  handleBackupList,
  handlePostbackup,
  handleRemoveBackup,
  handleRestoreBackup,
} from "../Context/Controller";
import Loading from "../components/Loading";
import "../css/BackupModal.css";

const BackupModal = ({ isOpen, onClose, agentId, containerId }) => {
  const [backupList, setBackupList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const fetchBackupList = async () => {
    setLoading(true);
    setError("");
    console.log(
      "Fetching backup list for agentId:",
      agentId,
      "containerId:",
      containerId
    );
    const result = await handleBackupList(agentId, containerId, setError);
    if (result.success) {
      let backups = result.data;
      console.log("Raw backups data:", backups);
      if (Array.isArray(backups)) {
        backups = backups.map((item, index) => ({
          id: item.id || index,
          name: item.name || JSON.stringify(item),
        }));
      } else if (typeof backups === "object" && !Array.isArray(backups)) {
        backups = Object.keys(backups).map((key) => ({
          id: key,
          name: backups[key] || key,
        }));
      } else {
        backups = [];
      }

      const parsedBackups = backups.map((backup) => {
        const parts = backup.name.split("_");
        let serviceName = "";
        let datePart = "";
        let timePart = "";

        if (parts.length >= 5) {
          serviceName = parts[2];
          datePart = `${parts[3]}/${parts[4]}/${parts[5]}`;
          timePart = `${parts[6]}:${parts[7]}:${parts[8]}`;
        }

        return {
          ...backup,
          service: serviceName,
          date: datePart,
          time: timePart,
        };
      });
      setBackupList(parsedBackups);
      console.log("Parsed backup list:", parsedBackups);
    } else {
      setBackupList([]);
      console.log("Failed to fetch backup list, setting empty array");
    }
    setLoading(false);
  };

  useEffect(() => {
    if (isOpen) {
      fetchBackupList();
    }
  }, [isOpen, agentId, containerId]);

  if (!isOpen) return null;

  const handleDeleteBackup = async (backupId) => {
    console.log("Delete button clicked, backupId:", backupId);
    if (!backupList.length || backupId < 0 || backupId >= backupList.length) {
      setError("No backups available or invalid backup ID");
      console.log("Invalid backupId, length:", backupList.length);
      return;
    }
    const backupName = backupList[backupId]?.name || "Unknown Backup";
    console.log("Confirming deletion of:", backupName);
    if (
      !window.confirm(`Are you sure you want to delete backup ${backupName}?`)
    ) {
      console.log("Deletion cancelled by user");
      return;
    }
    setLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      console.log(`Sending delete request for backup: ${backupName}`);
      const result = await handleRemoveBackup(
        agentId,
        containerId,
        backupName,
        setError
      );
      if (result.success) {
        setSuccessMessage(result.message);
        await fetchBackupList();
      }
    } catch (err) {
      setError(`Error deleting backup: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Đổi tên function để tránh nhầm lẫn (tùy chọn)
  const handleUserRestore = async (backupId) => {
    console.log("Restore button clicked, backupId:", backupId);
    if (!backupList.length || backupId < 0 || backupId >= backupList.length) {
      setError("No backups available or invalid backup ID");
      console.log("Invalid backupId, length:", backupList.length);
      return;
    }
    const backupName = backupList[backupId]?.name || "Unknown Backup";
    console.log("Confirming restoration of:", backupName);
    if (
      !window.confirm(`Are you sure you want to restore backup ${backupName}?`)
    ) {
      console.log("Restoration cancelled by user");
      return;
    }
    setLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      console.log(`Sending restore request for backup: ${backupName}`);
      const result = await handleRestoreBackup(
        agentId,
        containerId,
        backupName,
        "data",
        setError
      );
      console.log("Restore result:", result);
      if (result.success) {
        setSuccessMessage(result.message);
      } else {
        setError(`Restore failed: ${result.error || "Unknown error"}`);
      }
    } catch (err) {
      setError(`Error restoring backup: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!containerId) return;
    setLoading(true);
    setError("");
    setSuccessMessage("");
    try {
      const result = await handlePostbackup(agentId, containerId, setError);
      if (result.success) {
        console.log(`Backup created: ${result.data}`);
        setSuccessMessage(result.message);
        await fetchBackupList();
      }
    } catch (err) {
      setError(`Error creating backup: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="backup_title">
          <h3>Backup List</h3>
          <button
            className="add_backup"
            onClick={handleSave}
            disabled={loading}
          >
            +
          </button>
        </div>
        {loading && <Loading />}
        {error && <p className="error">{error}</p>}
        {successMessage && <p className="success-message">{successMessage}</p>}

        {!loading &&
          !error &&
          backupList.length === 1 &&
          backupList[0].name === "none" && <p>No backups available</p>}

        {!loading &&
          !error &&
          backupList.length > 0 &&
          backupList[0].name != "none" && (
            <ul className="backup-list">
              {backupList.map((backup, index) => (
                <li key={backup.id} className="backup-item">
                  <span className="backup-service">{backup.service}</span>
                  <span className="backup-date">{backup.date}</span>
                  <span className="backup-time">{backup.time}</span>
                  <div className="backup-actions">
                    <button
                      className="backup-btn delete-btn"
                      onClick={() => handleDeleteBackup(index)}
                      disabled={loading || !backupList.length}
                    >
                      Delete
                    </button>
                    <button
                      className="backup-btn restore-btn"
                      onClick={() => handleUserRestore(index)} // Sử dụng tên mới
                      disabled={loading || !backupList.length}
                    >
                      Restore
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

        <button className="modal-close-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
};

export default BackupModal;
