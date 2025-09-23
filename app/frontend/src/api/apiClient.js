import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:4000" || "", // e.g. "http://localhost:5000"
  headers: { "Content-Type": "application/json" },
  // timeout: 10000,
});

export default api;