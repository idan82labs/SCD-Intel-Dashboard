"use client";

import dynamic from "next/dynamic";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

// Dynamic import for Plotly (client-side only)
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => <Skeleton className="h-64 w-full" />,
});

interface ChartWrapperProps {
  type: string;
  data: Record<string, unknown>;
  title?: string;
}

export function ChartWrapper({ type, data, title }: ChartWrapperProps) {
  const renderChart = () => {
    switch (type) {
      case "bar_chart":
        return renderBarChart(data);
      case "line_chart":
        return renderLineChart(data);
      case "pie_chart":
        return renderPieChart(data);
      case "area_chart":
        return renderAreaChart(data);
      case "metric":
        return renderMetric(data);
      case "table":
        return renderTable(data);
      default:
        return <div className="p-4 text-muted-foreground">Unsupported chart type: {type}</div>;
    }
  };

  return (
    <Card className="p-4">
      {title && <h4 className="text-sm font-medium mb-4">{title}</h4>}
      {renderChart()}
    </Card>
  );
}

function renderBarChart(data: Record<string, unknown>) {
  const chartData = data as {
    labels?: string[];
    values?: number[];
    x?: string[];
    y?: number[];
    xLabel?: string;
    yLabel?: string;
  };

  const plotData = [
    {
      type: "bar" as const,
      x: chartData.labels || chartData.x || [],
      y: chartData.values || chartData.y || [],
      marker: {
        color: "hsl(222.2 47.4% 11.2%)",
      },
    },
  ];

  const layout = {
    autosize: true,
    margin: { t: 20, r: 20, b: 60, l: 60 },
    xaxis: { title: chartData.xLabel || "" },
    yaxis: { title: chartData.yLabel || "" },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { family: "inherit", size: 12 },
  };

  return (
    <Plot
      data={plotData}
      layout={layout}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%", height: "300px" }}
    />
  );
}

function renderLineChart(data: Record<string, unknown>) {
  const chartData = data as {
    labels?: string[];
    values?: number[];
    x?: string[];
    y?: number[];
    series?: { name: string; x?: string[]; y: number[] }[];
    xLabel?: string;
    yLabel?: string;
  };

  const traces = chartData.series
    ? chartData.series.map((series) => ({
        type: "scatter" as const,
        mode: "lines+markers" as const,
        name: series.name,
        x: series.x || chartData.x || chartData.labels || [],
        y: series.y,
        line: { width: 2 },
      }))
    : [
        {
          type: "scatter" as const,
          mode: "lines+markers" as const,
          x: chartData.x || chartData.labels || [],
          y: chartData.y || chartData.values || [],
          line: { width: 2, color: "hsl(222.2 47.4% 11.2%)" },
        },
      ];

  const layout = {
    autosize: true,
    margin: { t: 20, r: 20, b: 60, l: 60 },
    xaxis: { title: chartData.xLabel || "" },
    yaxis: { title: chartData.yLabel || "" },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { family: "inherit", size: 12 },
    showlegend: (chartData.series?.length || 0) > 1,
  };

  return (
    <Plot
      data={traces}
      layout={layout}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%", height: "300px" }}
    />
  );
}

function renderPieChart(data: Record<string, unknown>) {
  const chartData = data as {
    labels?: string[];
    values?: number[];
  };

  const plotData = [
    {
      type: "pie" as const,
      labels: chartData.labels || [],
      values: chartData.values || [],
      hole: 0.4,
      marker: {
        colors: [
          "#1e293b",
          "#475569",
          "#64748b",
          "#10b981",
          "#f59e0b",
          "#ef4444",
          "#8b5cf6",
        ],
      },
    },
  ];

  const layout = {
    autosize: true,
    margin: { t: 20, r: 20, b: 20, l: 20 },
    paper_bgcolor: "transparent",
    font: { family: "inherit", size: 12 },
    showlegend: true,
    legend: { orientation: "h" as const, y: -0.1 },
  };

  return (
    <Plot
      data={plotData}
      layout={layout}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%", height: "300px" }}
    />
  );
}

function renderAreaChart(data: Record<string, unknown>) {
  const chartData = data as {
    x?: string[];
    y?: number[];
    series?: { name: string; x?: string[]; y: number[] }[];
  };

  const traces = chartData.series
    ? chartData.series.map((series) => ({
        type: "scatter" as const,
        mode: "lines" as const,
        name: series.name,
        x: series.x || chartData.x || [],
        y: series.y,
        fill: "tozeroy" as const,
        stackgroup: "one",
      }))
    : [
        {
          type: "scatter" as const,
          mode: "lines" as const,
          x: chartData.x || [],
          y: chartData.y || [],
          fill: "tozeroy" as const,
        },
      ];

  const layout = {
    autosize: true,
    margin: { t: 20, r: 20, b: 60, l: 60 },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { family: "inherit", size: 12 },
  };

  return (
    <Plot
      data={traces}
      layout={layout}
      config={{ responsive: true, displayModeBar: false }}
      style={{ width: "100%", height: "300px" }}
    />
  );
}

function renderMetric(data: Record<string, unknown>) {
  const chartData = data as {
    metrics?: { label: string; value: string | number; change?: number }[];
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {chartData.metrics?.map((metric, index) => (
        <div key={index} className="p-4 bg-muted/50 rounded-lg text-center">
          <div className="text-2xl font-bold text-primary">{metric.value}</div>
          <div className="text-sm text-muted-foreground mt-1">{metric.label}</div>
          {metric.change !== undefined && (
            <div
              className={`text-xs mt-1 ${
                metric.change > 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {metric.change > 0 ? "↑" : "↓"} {Math.abs(metric.change)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function renderTable(data: Record<string, unknown>) {
  const chartData = data as {
    columns?: string[];
    rows?: (string | number)[][];
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            {chartData.columns?.map((col, index) => (
              <th key={index} className="text-left p-2 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {chartData.rows?.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b last:border-0">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="p-2">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
