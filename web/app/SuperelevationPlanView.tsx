"use client";

/* Pyodide service responses are JSON dictionaries. */
/* eslint-disable @typescript-eslint/no-explicit-any */

import { PointerEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

type Dict = Record<string, any>;
type ViewBox = { x: number; y: number; width: number; height: number };

function cadColor(aci: number) {
  return ({ 7: "#f2f2f2", 8: "#808080", 10: "#ff0000" } as Record<number, string>)[aci] || "#d8d8d8";
}

function cadLineweight(lineweight: number) {
  if (!Number.isFinite(lineweight) || lineweight <= 0) return 1;
  return Math.max(0.75, Math.min(3, lineweight / 20));
}

function fittedView(plan: Dict): ViewBox {
  const bounds = plan.bounds || {};
  const width = Math.max(Number(bounds.max_x || 1) - Number(bounds.min_x || 0), 1);
  const height = Math.max(Number(bounds.max_y || 1) - Number(bounds.min_y || 0), 1);
  const padding = Math.max(width, height) * 0.06;
  return {
    x: Number(bounds.min_x || 0) - padding,
    y: -Number(bounds.max_y || 1) - padding,
    width: width + padding * 2,
    height: height + padding * 2,
  };
}

export default function SuperelevationPlanView({ plan }: { plan: Dict }) {
  const fitted = useMemo(() => fittedView(plan), [plan]);
  const [view, setView] = useState<ViewBox>(fitted);
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const viewportRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ x: number; y: number; view: ViewBox } | null>(null);

  const zoom = useCallback((factor: number, anchorX = 0.5, anchorY = 0.5) => {
    const nextWidth = Math.min(fitted.width * 10, Math.max(fitted.width / 300, view.width * factor));
    const nextHeight = Math.min(fitted.height * 10, Math.max(fitted.height / 300, view.height * factor));
    setView({
      x: view.x + (view.width - nextWidth) * anchorX,
      y: view.y + (view.height - nextHeight) * anchorY,
      width: nextWidth,
      height: nextHeight,
    });
  }, [fitted, view]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const wheelZoom = (event: WheelEvent) => {
      event.preventDefault();
      const bounds = viewport.getBoundingClientRect();
      zoom(
        event.deltaY < 0 ? 0.78 : 1.28,
        Math.max(0, Math.min(1, (event.clientX - bounds.left) / Math.max(bounds.width, 1))),
        Math.max(0, Math.min(1, (event.clientY - bounds.top) / Math.max(bounds.height, 1))),
      );
    };
    viewport.addEventListener("wheel", wheelZoom, { passive: false });
    return () => viewport.removeEventListener("wheel", wheelZoom);
  }, [zoom]);

  const startPan = (event: PointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    setSelectedGroup(null);
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = { x: event.clientX, y: event.clientY, view: { ...view } };
    setDragging(true);
  };

  const movePan = (event: PointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    setView({
      ...drag.view,
      x: drag.view.x - (event.clientX - drag.x) * drag.view.width / Math.max(bounds.width, 1),
      y: drag.view.y - (event.clientY - drag.y) * drag.view.height / Math.max(bounds.height, 1),
    });
  };

  const endPan = (event: PointerEvent<HTMLDivElement>) => {
    if (dragRef.current && event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    dragRef.current = null;
    setDragging(false);
  };

  const selected = (plan.entities || []).find(
    (entity: Dict) => entity.preview?.group_id === selectedGroup,
  )?.preview || null;
  const selectEntity = (entity: Dict) => {
    if (entity.preview?.group_id) setSelectedGroup(entity.preview.group_id);
  };
  const layerStyle = (entity: Dict) => plan.layers?.[entity.layer] || {};

  return <div className="plan-layout">
    <div className="plan-frame">
      <div className="plan-tools"><span>{plan.alignment_name} · {(plan.entities || []).length} CAD entities</span><button title="Zoom out" aria-label="Plan zoom out" onClick={() => zoom(1.28)}>−</button><button title="Zoom in" aria-label="Plan zoom in" onClick={() => zoom(0.78)}>+</button><button title="Fit drawing" onClick={() => setView(fitted)}>Fit</button></div>
      <div ref={viewportRef} className={`plan-canvas${dragging ? " dragging" : ""}`} onPointerDown={startPan} onPointerMove={movePan} onPointerUp={endPan} onPointerCancel={endPan}>
        <svg viewBox={`${view.x} ${view.y} ${view.width} ${view.height}`} role="img" aria-label="CAD model-space preview of the overlay DXF">
          {(plan.entities || []).map((entity: Dict) => {
            const style = layerStyle(entity);
            const isSelected = Boolean(selectedGroup && entity.preview?.group_id === selectedGroup);
            const selectable = Boolean(entity.preview?.group_id);
            const onEntityPointerDown = (event: PointerEvent<SVGElement>) => {
              if (selectable) event.stopPropagation();
            };
            if (entity.type === "LINE") {
              return <line
                key={entity.id}
                className={`cad-line${selectable ? " selectable" : ""}`}
                data-selected={isSelected || undefined}
                x1={entity.x1}
                y1={-entity.y1}
                x2={entity.x2}
                y2={-entity.y2}
                stroke={isSelected ? "#00e5ff" : cadColor(Number(style.color))}
                strokeWidth={cadLineweight(Number(style.lineweight))}
                vectorEffect="non-scaling-stroke"
                strokeLinecap="square"
                onPointerDown={onEntityPointerDown}
                onClick={() => selectEntity(entity)}
              />;
            }
            if (entity.type === "TEXT") {
              return <text
                key={entity.id}
                className={`cad-text${selectable ? " selectable" : ""}`}
                data-selected={isSelected || undefined}
                x={entity.x}
                y={-entity.y}
                fill={isSelected ? "#00e5ff" : cadColor(Number(style.color))}
                fontSize={entity.height}
                textAnchor={entity.alignment === "RIGHT" ? "end" : "start"}
                transform={`rotate(${-Number(entity.rotation || 0)} ${entity.x} ${-entity.y})`}
                onPointerDown={onEntityPointerDown}
                onClick={() => selectEntity(entity)}
              >{entity.text}</text>;
            }
            return null;
          })}
        </svg>
      </div>
    </div>
    <aside className="plan-inspector">
      <div className="inspector-heading"><span>{selected?.station ? "DXF callout" : "Plan view"}</span><strong>{selected?.curve_name || plan.alignment_name}</strong><small>{selected?.station || plan.coordinate_system?.display_name || "Coordinate system not declared"}</small></div>
      {selected?.station ? <dl className="cad-properties"><div><dt>Curve</dt><dd>{selected.curve_name}</dd></div><div><dt>Station</dt><dd>{selected.station}</dd></div><div><dt>Side</dt><dd>{selected.side || "Not provided"}</dd></div><div><dt>Slope</dt><dd>{selected.slope || "Not provided"}</dd></div><div><dt>Event</dt><dd>{selected.event_type || "Not provided"}</dd></div></dl> : selected ? <p className="inspector-empty">Curve title group selected.</p> : <p className="inspector-empty">Select a CAD callout or curve title to inspect its shared DXF metadata.</p>}
      {(plan.errors || []).length > 0 && <div className="plan-issues"><strong>DXF blocked</strong><span>{plan.errors.length} overlay issue{plan.errors.length === 1 ? "" : "s"}</span></div>}
    </aside>
  </div>;
}
