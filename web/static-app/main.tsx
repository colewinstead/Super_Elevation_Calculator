import { createRoot } from "react-dom/client";

import CalculatorApp from "../app/CalculatorApp";
import "../app/globals.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("The calculator root element is missing.");
}

createRoot(root).render(<CalculatorApp />);
