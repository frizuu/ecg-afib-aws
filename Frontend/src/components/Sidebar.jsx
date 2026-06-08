import { Link, useLocation, useNavigate } from "react-router-dom";

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("patientName");
    localStorage.removeItem("history");

    navigate("/");
  };

  const menuStyle = (path) => ({
    display: "block",
    padding: "12px 16px",
    borderRadius: "10px",
    textDecoration: "none",
    color:
      location.pathname === path
        ? "#ffffff"
        : "#94a3b8",
    background:
      location.pathname === path
        ? "#2563eb"
        : "transparent",
    fontWeight:
      location.pathname === path
        ? "600"
        : "400",
    transition: "0.3s",
  });

  return (
    <div
      style={{
        width: "260px",
        background: "#0f172a",
        minHeight: "100vh",
        borderRight: "1px solid #1e293b",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <div>
        <div
          style={{
            padding: "24px",
            borderBottom:
              "1px solid #1e293b",
          }}
        >
          <h2
            style={{
              margin: 0,
              color: "white",
            }}
          >
            ❤️ ECG Monitor
          </h2>

          <p
            style={{
              marginTop: "8px",
              color: "#94a3b8",
              fontSize: "13px",
            }}
          >
            AFIB Detection System
          </p>
        </div>

        <div
          style={{
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          <Link
            to="/dashboard"
            style={menuStyle(
              "/dashboard"
            )}
          >
            📊 Dashboard
          </Link>

          <Link
            to="/history"
            style={menuStyle(
              "/history"
            )}
          >
            🕒 History
          </Link>

          <Link
            to="/analytics"
            style={menuStyle(
              "/analytics"
            )}
          >
            📉 Analytics
          </Link>

          <Link
            to="/alerts"
            style={menuStyle(
              "/alerts"
            )}
          >
            🚨 Alerts
          </Link>
        </div>
      </div>

      <div
        style={{
          padding: "20px",
        }}
      >
        <button
          onClick={handleLogout}
          style={{
            width: "100%",
            padding: "12px",
            border: "none",
            borderRadius: "10px",
            background: "#dc2626",
            color: "white",
            cursor: "pointer",
            fontWeight: "600",
          }}
        >
          Logout
        </button>
      </div>
    </div>
  );
}