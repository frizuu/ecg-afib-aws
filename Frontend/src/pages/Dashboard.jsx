import {
  useEffect,
  useRef,
  useState,
} from "react";

import { Navigate } from "react-router-dom";

import "../App.css";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import Sidebar from "../components/Sidebar";

import {
  getLatest,
  getStreamLatest,
  normalizePrediction,
  startStream,
  stopStream,
  getStreamStatus,
  predictStream,
} from "../services/api";

export default function Dashboard() {
  const patientName =
    localStorage.getItem("patientName");

  const intervalRef =
    useRef(null);

  const [ecgData, setEcgData] =
    useState([]);

  const [status, setStatus] =
    useState("Waiting");

  const [bpm, setBpm] =
    useState("--");

  const [risk, setRisk] =
    useState("--");

  const [alerts, setAlerts] =
    useState(0);

  const [lastLabel, setLastLabel] =
    useState("");

  const [lastUpdate, setLastUpdate] =
    useState("-");

  const [isMonitoring, setIsMonitoring] =
    useState(false);

  const [isLoading, setIsLoading] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  if (!patientName) {
    return <Navigate to="/" />;
  }

  const savePredictionToDashboard =
    (prediction) => {
      if (!prediction) return;

      const record =
        normalizePrediction(
          prediction,
          patientName
        );

      setStatus(record.status);
      setBpm(record.bpm);
      setRisk(record.risk);
      setLastUpdate(record.timestamp);

      if (
        prediction.label ===
          "AFIB" &&
        lastLabel !== "AFIB"
      ) {
        setAlerts(
          (prev) => prev + 1
        );
      }

      const history =
        JSON.parse(
          localStorage.getItem(
            "history"
          ) || "[]"
        );

      const latestRecord =
        history[0];

      if (
        !latestRecord ||
        latestRecord.timestamp !==
          record.timestamp
      ) {
        history.unshift(record);

        localStorage.setItem(
          "history",
          JSON.stringify(
            history.slice(0, 100)
          )
        );
      }

      setLastLabel(
        prediction.label
      );
    };

  const loadLatest = async () => {
    try {
      const response =
        await getLatest();

      savePredictionToDashboard(
        response?.last_prediction
      );
    } catch (err) {
      console.error(err);
    }
  };

  const loadStreamSignal =
    async () => {
      const response =
        await getStreamLatest(5);

      const signal =
        response?.signal || [];

      setEcgData(
        signal.map(
          (value, index) => ({
            time: index,
            value,
          })
        )
      );
    };

  const stopSignalPolling =
    () => {
      if (intervalRef.current) {
        clearInterval(
          intervalRef.current
        );
        intervalRef.current = null;
      }
    };

  const startSignalPolling =
    () => {
      stopSignalPolling();

      intervalRef.current =
        setInterval(
          async () => {
            try {
              await loadStreamSignal();
            } catch (err) {
              console.error(err);
            }
          },
          2000
        );
    };

  useEffect(() => {
    const initializeDashboard =
      async () => {
        await loadLatest();

        try {
          const streamStatus =
            await getStreamStatus();

          setIsMonitoring(
            Boolean(
              streamStatus?.running
            )
          );

          if (streamStatus?.running) {
            startSignalPolling();
            await loadStreamSignal();
          }
        } catch (err) {
          console.error(err);
        }
      };

    initializeDashboard();
  }, []);

  useEffect(() => {
    return () => {
      stopSignalPolling();
    };
  }, []);

  const handleStart =
    async () => {
      setIsLoading(true);
      setError("");
      setMessage("");

      try {
        await startStream(false);

        setIsMonitoring(true);
        setMessage(
          "Stream ECG berhasil dimulai."
        );

        startSignalPolling();
        await loadStreamSignal();
      } catch (err) {
        console.error(err);
        setError(
          err.message ||
            "Gagal memulai stream."
        );
      } finally {
        setIsLoading(false);
      }
    };

  const handlePredict =
    async () => {
      setIsLoading(true);
      setError("");
      setMessage("");

      try {
        const prediction =
          await predictStream();

        savePredictionToDashboard(
          prediction
        );
        await loadStreamSignal();

        setMessage(
          `Prediksi selesai: ${prediction.label}`
        );
      } catch (err) {
        console.error(err);
        setError(
          err.message ||
            "Gagal menjalankan prediksi."
        );
      } finally {
        setIsLoading(false);
      }
    };

  const handleStop =
    async () => {
      setIsLoading(true);
      setError("");
      setMessage("");

      try {
        await stopStream();

        stopSignalPolling();
        setIsMonitoring(false);
        setMessage(
          "Stream ECG berhasil dihentikan."
        );
      } catch (err) {
        console.error(err);
        setError(
          err.message ||
            "Gagal menghentikan stream."
        );
      } finally {
        setIsLoading(false);
      }
    };

  return (
    <div className="dashboard-container">
      <Sidebar />

      <main className="main-content">
        <div className="header">
          <h1>
            AFIB Detection Dashboard
          </h1>

          <p>
            Welcome, {patientName}
          </p>
        </div>

        <section className="primary-actions">
          <button
            className="action-button action-start"
            disabled={
              isLoading ||
              isMonitoring
            }
            onClick={handleStart}
          >
            Stream Start
          </button>

          <button
            className="action-button action-predict"
            disabled={
              isLoading ||
              !isMonitoring
            }
            onClick={handlePredict}
          >
            Predict AFIB / Normal
          </button>

          <button
            className="action-button action-stop"
            disabled={
              isLoading ||
              !isMonitoring
            }
            onClick={handleStop}
          >
            Stream Stop
          </button>
        </section>

        {(message || error) && (
          <div
            className={
              error
                ? "status-banner status-banner-error"
                : "status-banner"
            }
          >
            {error || message}
          </div>
        )}

        <div className="cards">
          <div className="card">
            <h3>
              Stream Status
            </h3>
            <h2>
              {isMonitoring
                ? "ACTIVE"
                : "STOPPED"}
            </h2>
          </div>

          <div className="card">
            <h3>
              Prediction
            </h3>
            <h2>{status}</h2>
          </div>

          <div className="card">
            <h3>
              AFIB Risk
            </h3>
            <h2>{risk}%</h2>
          </div>

          <div className="card">
            <h3>
              Heart Rate
            </h3>
            <h2>
              {bpm} BPM
            </h2>
          </div>

          <div className="card">
            <h3>Alerts</h3>
            <h2>{alerts}</h2>
          </div>

          <div className="card">
            <h3>
              Last Update
            </h3>

            <h2 className="small-value">
              {lastUpdate}
            </h2>
          </div>
        </div>

        <div className="chart-card">
          <h2>
            Live ECG Stream
          </h2>

          <ResponsiveContainer
            width="100%"
            height={350}
          >
            <LineChart data={ecgData}>
              <XAxis
                dataKey="time"
                hide
              />

              <YAxis />

              <Tooltip />

              <Line
                type="monotone"
                dataKey="value"
                stroke="#00ff88"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </main>
    </div>
  );
}
