import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import Sidebar from "../components/Sidebar";
import {
  getHistory,
  normalizePrediction,
} from "../services/api";

export default function Alerts() {
  const patientName =
    localStorage.getItem("patientName");

  const [alertsData, setAlertsData] =
    useState([]);

  if (!patientName) {
    return <Navigate to="/" />;
  }

  const loadAlerts = async () => {
    let history = [];

    try {
      const response =
        await getHistory();

      history =
        (response?.items || []).map(
          (item) =>
            normalizePrediction(
              item,
              patientName
            )
        );
    } catch (err) {
      console.error(err);

      history =
        JSON.parse(
          localStorage.getItem(
            "history"
          ) || "[]"
        );
    }

    const filteredAlerts =
      history.filter((item) => {
        const bpm =
          Number(item.bpm) || 0;

        const risk =
          Number(item.risk) || 0;

        return (
          item.status === "AFIB" ||
          risk >= 80 ||
          bpm >= 140
        );
      });

    setAlertsData(filteredAlerts);
  };

  const getSeverity = (
    item
  ) => {
    const bpm =
      Number(item.bpm) || 0;

    const risk =
      Number(item.risk) || 0;

    if (
      item.status === "AFIB" ||
      risk >= 80
    ) {
      return "HIGH";
    }

    if (
      bpm >= 140 &&
      bpm <= 160
    ) {
      return "MEDIUM";
    }

    return "LOW";
  };

  useEffect(() => {
    loadAlerts();

    const interval =
      setInterval(() => {
        loadAlerts();
      }, 10000);

    return () =>
      clearInterval(interval);
  }, []);

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
          🚨 AFIB Alerts
        </h1>

        <p>
          Monitoring critical
          events and abnormal
          heart activity
        </p>

        <div
          style={{
            background:
              "#0f172a",
            borderRadius:
              "12px",
            overflow:
              "hidden",
            marginTop:
              "20px",
          }}
        >
          <table
            style={{
              width: "100%",
              borderCollapse:
                "collapse",
            }}
          >
            <thead>
              <tr
                style={{
                  background:
                    "#1e293b",
                }}
              >
                <th
                  style={{
                    padding:
                      "15px",
                  }}
                >
                  Timestamp
                </th>

                <th
                  style={{
                    padding:
                      "15px",
                  }}
                >
                  Severity
                </th>

                <th
                  style={{
                    padding:
                      "15px",
                  }}
                >
                  Status
                </th>

                <th
                  style={{
                    padding:
                      "15px",
                  }}
                >
                  BPM
                </th>

                <th
                  style={{
                    padding:
                      "15px",
                  }}
                >
                  Risk
                </th>

                <th
                  style={{
                    padding:
                      "15px",
                  }}
                >
                  Patient
                </th>
              </tr>
            </thead>

            <tbody>
              {alertsData.length ===
              0 ? (
                <tr>
                  <td
                    colSpan="6"
                    style={{
                      textAlign:
                        "center",
                      padding:
                        "30px",
                    }}
                  >
                    No alerts
                    detected
                  </td>
                </tr>
              ) : (
                alertsData.map(
                  (
                    item,
                    index
                  ) => {
                    const severity =
                      getSeverity(
                        item
                      );

                    return (
                      <tr
                        key={
                          item.timestamp ||
                          index
                        }
                        style={{
                          borderBottom:
                            "1px solid #334155",
                        }}
                      >
                        <td
                          style={{
                            padding:
                              "15px",
                          }}
                        >
                          {
                            item.timestamp
                          }
                        </td>

                        <td
                          style={{
                            padding:
                              "15px",
                            fontWeight:
                              "bold",
                            color:
                              severity ===
                              "HIGH"
                                ? "#ef4444"
                                : severity ===
                                  "MEDIUM"
                                ? "#f59e0b"
                                : "#10b981",
                          }}
                        >
                          {
                            severity
                          }
                        </td>

                        <td
                          style={{
                            padding:
                              "15px",
                          }}
                        >
                          {
                            item.status
                          }
                        </td>

                        <td
                          style={{
                            padding:
                              "15px",
                          }}
                        >
                          {item.bpm}
                        </td>

                        <td
                          style={{
                            padding:
                              "15px",
                          }}
                        >
                          {
                            item.risk
                          }
                          %
                        </td>

                        <td
                          style={{
                            padding:
                              "15px",
                          }}
                        >
                          {
                            item.patient
                          }
                        </td>
                      </tr>
                    );
                  }
                )
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
