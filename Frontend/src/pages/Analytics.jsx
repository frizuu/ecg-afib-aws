import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";

import Sidebar from "../components/Sidebar";

export default function Analytics() {
  const patientName =
    localStorage.getItem("patientName");

  const [historyData, setHistoryData] =
    useState([]);

  if (!patientName) {
    return <Navigate to="/" />;
  }

  useEffect(() => {
    const loadAnalytics =
      () => {
        const history =
          JSON.parse(
            localStorage.getItem(
              "history"
            ) || "[]"
          );

        setHistoryData(
          history.reverse()
        );
      };

    loadAnalytics();

    const interval =
      setInterval(() => {
        loadAnalytics();
      }, 10000);

    return () =>
      clearInterval(interval);
  }, []);

  const totalRecords =
    historyData.length;

  const afibCount =
    historyData.filter(
      (item) =>
        item.status === "AFIB"
    ).length;

  const normalCount =
    historyData.filter(
      (item) =>
        item.status ===
        "Normal"
    ).length;

  const averageBPM =
    totalRecords > 0
      ? Math.round(
          historyData.reduce(
            (
              sum,
              item
            ) =>
              sum +
              Number(
                item.bpm || 0
              ),
            0
          ) / totalRecords
        )
      : 0;

  const highestBPM =
    totalRecords > 0
      ? Math.max(
          ...historyData.map(
            (item) =>
              Number(
                item.bpm || 0
              )
          )
        )
      : 0;

  const pieData = [
    {
      name: "Normal",
      value: normalCount,
    },
    {
      name: "AFIB",
      value: afibCount,
    },
  ];

  const COLORS = [
    "#10b981",
    "#ef4444",
  ];

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        background: "#031235",
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
        <h1>
          Analytics Dashboard
        </h1>

        <p>
          ECG Monitoring
          Statistics &
          Trends
        </p>

        <div className="cards">
          <div className="card">
            <h3>
              Total Records
            </h3>

            <h2>
              {totalRecords}
            </h2>
          </div>

          <div className="card">
            <h3>
              AFIB Events
            </h3>

            <h2>
              {afibCount}
            </h2>
          </div>

          <div className="card">
            <h3>
              Average BPM
            </h3>

            <h2>
              {averageBPM}
            </h2>
          </div>

          <div className="card">
            <h3>
              Highest BPM
            </h3>

            <h2>
              {highestBPM}
            </h2>
          </div>
        </div>

        <div
          className="chart-card"
          style={{
            marginTop: "25px",
          }}
        >
          <h2>
            Heart Rate Trend
          </h2>

          <ResponsiveContainer
            width="100%"
            height={300}
          >
            <LineChart
              data={
                historyData
              }
            >
              <XAxis
                dataKey="timestamp"
                hide
              />

              <YAxis />

              <Tooltip />

              <Line
                type="monotone"
                dataKey="bpm"
                stroke="#00ff88"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div
          className="chart-card"
          style={{
            marginTop: "25px",
          }}
        >
          <h2>
            AFIB Risk Trend
          </h2>

          <ResponsiveContainer
            width="100%"
            height={300}
          >
            <LineChart
              data={
                historyData
              }
            >
              <XAxis
                dataKey="timestamp"
                hide
              />

              <YAxis />

              <Tooltip />

              <Line
                type="monotone"
                dataKey="risk"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div
          className="chart-card"
          style={{
            marginTop: "25px",
          }}
        >
          <h2>
            Prediction
            Distribution
          </h2>

          <ResponsiveContainer
            width="100%"
            height={300}
          >
            <PieChart>
              <Pie
                data={
                  pieData
                }
                cx="50%"
                cy="50%"
                outerRadius={
                  100
                }
                dataKey="value"
                label
              >
                {pieData.map(
                  (
                    entry,
                    index
                  ) => (
                    <Cell
                      key={
                        index
                      }
                      fill={
                        COLORS[
                          index
                        ]
                      }
                    />
                  )
                )}
              </Pie>

              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}