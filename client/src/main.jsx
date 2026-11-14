import React from "react";
import { createRoot } from "react-dom/client";
import { EquipmentRentalApp } from "./app.jsx";
import "./style.css";

const container = document.getElementById("content");
const root = createRoot(container);
root.render(<EquipmentRentalApp />);
