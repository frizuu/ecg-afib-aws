import { useState } from "react";

export default function Login() {
  const [name, setName] = useState("");

  const startMonitoring = () => {
    if (!name) {
      alert("Masukkan nama pasien");
      return;
    }

    localStorage.setItem("patientName", name);

    window.location.href = "/dashboard";
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "#0f172a",
      }}
    >
      <div
        style={{
          background: "#1e293b",
          padding: 40,
          borderRadius: 12,
          width: 450,
        }}
      >
        <h1>❤️ Smart ECG Monitoring</h1>

        <p style={{ marginTop: 10 }}>
          Masukkan nama pasien untuk memulai monitoring
        </p>

        <input
          type="text"
          placeholder="Nama Pasien"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{
            width: "100%",
            marginTop: 20,
            padding: 12,
          }}
        />

        <button
          onClick={startMonitoring}
          style={{
            width: "100%",
            marginTop: 20,
            padding: 12,
          }}
        >
          Start Monitoring
        </button>
      </div>
    </div>
  );
}