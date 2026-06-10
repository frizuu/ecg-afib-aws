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

const STREAM_WINDOW_SECONDS = 5;
const PREDICTION_THRESHOLD = 0.55;
const MIN_PREDICTION_SAMPLES = 100;

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

  const [isStreaming, setIsStreaming] =
    useState(false);

  const [streamSamples, setStreamSamples] =
    useState(0);

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
        await getStreamLatest(
          STREAM_WINDOW_SECONDS
        );

      const signal =
        response?.signal || [];

      setIsStreaming(
        Boolean(response?.running)
      );
      setStreamSamples(
        response?.metadata
          ?.available_samples ||
          signal.length
      );
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

          setIsStreaming(
            Boolean(
              streamStatus?.running
            )
          );
          setStreamSamples(
            streamStatus?.buffered_samples ||
              0
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

        setIsStreaming(true);
        setMessage(
          "Stream ECG dimulai. Data sedang digenerate."
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
          await predictStream(
            STREAM_WINDOW_SECONDS,
            PREDICTION_THRESHOLD
          );

        savePredictionToDashboard(
          prediction
        );
        await loadStreamSignal();

        setMessage(
          `Prediksi ${STREAM_WINDOW_SECONDS} detik terakhir selesai: ${prediction.label}`
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
        setIsStreaming(false);
        setMessage(
          "Stream ECG dihentikan. Generate data berhenti."
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
              isStreaming
            }
            onClick={handleStart}
          >
            Start Stream
          </button>

          <button
            className="action-button action-predict"
            disabled={
              isLoading ||
              !isStreaming ||
              streamSamples <
                MIN_PREDICTION_SAMPLES
            }
            onClick={handlePredict}
          >
            Predict
          </button>

          <button
            className="action-button action-stop"
            disabled={
              isLoading ||
              !isStreaming
            }
            onClick={handleStop}
          >
            Stop Stream
          </button>
        </section>

        <div className="stream-config">
          <span>
            Prediction window:{" "}
            <strong>
              {STREAM_WINDOW_SECONDS}s
            </strong>
          </span>

          <span>
            Threshold:{" "}
            <strong>
              {PREDICTION_THRESHOLD}
            </strong>
          </span>

          <span>
            Samples ready:{" "}
            <strong>
              {streamSamples}
            </strong>
          </span>
        </div>

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
              {isStreaming
                ? "GENERATING"
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
