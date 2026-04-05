import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Patients from "./pages/Patients";
import PatientDetail from "./pages/PatientDetail";
import AIAssistant from "./pages/AIAssistant";
import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="patients" element={<Patients />} />
        <Route path="patients/:patientId" element={<PatientDetail />} />
        <Route path="assistant" element={<AIAssistant />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
