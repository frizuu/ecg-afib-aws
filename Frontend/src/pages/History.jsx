import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import Sidebar from "../components/Sidebar";
import {
  getHistory,
  normalizePrediction,
} from "../services/api";

export default function History() {
  const patientName =
    localStorage.getItem("patientName");

  const [historyData, setHistoryData] =
    useState([]);

  if (!patientName) {
    return <Navigate to="/" />;
  }

  const loadHistory = async () => {
    try {
      const response =
        await getHistory();

      const items =
        response?.items || [];

      setHistoryData(
        items.map((item) =>
          normalizePrediction(
            item,
            patientName
          )
        )
      );
    } catch (err) {
      console.error(err);

      const history =
        JSON.parse(
          localStorage.getItem(
            "history"
          ) || "[]"
        );

      setHistoryData(history);
    }
  };

  useEffect(() => {
    loadHistory();

    const interval =
      setInterval(() => {
        loadHistory();
      }, 5000);

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
          Prediction History
        </h1>

        <p>
          Patient: {patientName}
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
              {historyData.length ===
              0 ? (
                <tr>
                  <td
                    colSpan="5"
                    style={{
                      textAlign:
                        "center",
                      padding:
                        "30px",
                    }}
                  >
                    No prediction
                    history available
                  </td>
                </tr>
              ) : (
                historyData.map(
                  (
                    item,
                    index
                  ) => (
                    <tr
                      key={
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
                          color:
                            item.status ===
                            "AFIB"
                              ? "#ef4444"
                              : "#10b981",
                          fontWeight:
                            "bold",
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
                  )
                )
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
