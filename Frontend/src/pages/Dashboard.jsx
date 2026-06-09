import {
  useState,
  useEffect,
  useRef,
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

  if (!patientName) {
    return <Navigate to="/" />;
  }

  const loadLatest = async () => {
    try {
      const response =
        await getLatest();

      const prediction =
        response?.last_prediction;

      if (!prediction) return;

      const record =
        normalizePrediction(
          prediction,
          patientName
        );

      setStatus(
        record.status
      );

      setBpm(
        record.bpm
      );

      setRisk(
        record.risk
      );

      setLastUpdate(
        record.timestamp
      );

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

  useEffect(() => {
    loadLatest();
  }, []);

  useEffect(() => {
    return () => {
      if (
        intervalRef.current
      ) {
        clearInterval(
          intervalRef.current
        );
      }
    };
  }, []);

  const handleStart =
    async () => {
      try {
        if (
          intervalRef.current
        ) {
          clearInterval(
            intervalRef.current
          );
        }

        await startStream();

        setIsMonitoring(true);

        intervalRef.current =
          setInterval(
            async () => {
              try {
                await predictStream();

                await loadLatest();
                await loadStreamSignal();
              } catch (err) {
                console.error(
                  err
                );
              }
            },
            10000
          );
      } catch (err) {
        console.error(err);
      }
    };

  const handleStop =
    async () => {
      try {
        await stopStream();

        if (
          intervalRef.current
        ) {
          clearInterval(
            intervalRef.current
          );
        }

        setIsMonitoring(false);
      } catch (err) {
        console.error(err);
      }
    };

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        background:
          "#031235",
        color: "white",
      }}
    >
      <Sidebar />

      <div
        style={{
          flex: 1,
          padding: "30px",
        }}
      >
        <div className="header">
          <h1>
            AFIB Detection Dashboard
          </h1>

          <p>
            Welcome,{" "}
            {patientName}
          </p>
        </div>

        <div className="cards">
          <div className="card">
            <h3>Status</h3>
            <h2>{status}</h2>
          </div>

          <div className="card">
            <h3>Heart Rate</h3>
            <h2>
              {bpm} BPM
            </h2>
          </div>

          <div className="card">
            <h3>AFIB Risk</h3>
            <h2>{risk}%</h2>
          </div>

          <div className="card">
            <h3>Alerts</h3>
            <h2>{alerts}</h2>
          </div>

          <div className="card">
            <h3>Patient</h3>
            <h2>
              {patientName}
            </h2>
          </div>

          <div className="card">
            <h3>Monitoring</h3>
            <h2>
              {isMonitoring
                ? "ACTIVE"
                : "STOPPED"}
            </h2>
          </div>

          <div className="card">
            <h3>
              Last Update
            </h3>

            <h2
              style={{
                fontSize:
                  "16px",
              }}
            >
              {
                lastUpdate
              }
            </h2>
          </div>
        </div>

        <div className="chart-card">
          <h2>
            Live ECG Monitoring
          </h2>

          <ResponsiveContainer
            width="100%"
            height={350}
          >
            <LineChart
              data={ecgData}
            >
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

        <div
          className="card"
          style={{
            marginTop:
              "25px",
          }}
        >
          <h2>
            Prediction Result
          </h2>

          <p>
            Current Status:
            {" "}
            {status}
          </p>

          <p>
            Heart Rate:
            {" "}
            {bpm} BPM
          </p>

          <p>
            AFIB Risk:
            {" "}
            {risk}%
          </p>

          <p>
            Last Update:
            {" "}
            {lastUpdate}
          </p>

          <p>
            Monitoring:
            {" "}
            {isMonitoring
              ? "ACTIVE"
              : "STOPPED"}
          </p>
        </div>

        <div className="actions">
          <button
            onClick={
              handleStart
            }
          >
            Start Monitoring
          </button>

          <button
            className="danger"
            onClick={
              handleStop
            }
          >
            Stop Monitoring
          </button>
        </div>
      </div>
    </div>
  );
}
