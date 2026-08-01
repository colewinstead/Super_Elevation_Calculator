import calculators from "./generated/calculators.json";

export default function CalculatorCards() {
  return (
    <div className="calculator-card-grid">
      {calculators.map((calculator, index) => (
        <a className="calculator-card" href={calculator.route} key={calculator.id}>
          <div className="calculator-card-topline">
            <span>{calculator.category}</span>
            <b>{calculator.access}</b>
          </div>
          <div className={`calculator-card-symbol symbol-${calculator.id}`} aria-hidden="true">
            <i /><i /><i />
          </div>
          <span className="calculator-card-number">0{index + 1}</span>
          <h3>{calculator.title}</h3>
          <p>{calculator.description}</p>
          <div className="calculator-card-action"><span>Open calculator</span><b>↗</b></div>
        </a>
      ))}
    </div>
  );
}
