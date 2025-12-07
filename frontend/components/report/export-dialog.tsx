"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { exportReport } from "@/lib/api-client";
import { FileJson, FileSpreadsheet, Download, Loader2 } from "lucide-react";

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  sessionId: string;
}

const formats = [
  {
    id: "json",
    label: "JSON",
    description: "Structured data format",
    icon: FileJson,
  },
  {
    id: "csv",
    label: "CSV",
    description: "Spreadsheet compatible",
    icon: FileSpreadsheet,
  },
];

export function ExportDialog({ open, onClose, sessionId }: ExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState<"json" | "csv">("json");
  const [includeRawData, setIncludeRawData] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const blob = await exportReport(sessionId, selectedFormat, includeRawData);

      // Download the file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report_${sessionId}.${selectedFormat}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      onClose();
    } catch (error) {
      console.error("Export failed:", error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export Report</DialogTitle>
          <DialogDescription>
            Choose a format to download your research report.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Format Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Format</label>
            <div className="grid grid-cols-2 gap-2">
              {formats.map((format) => (
                <button
                  key={format.id}
                  onClick={() => setSelectedFormat(format.id as "json" | "csv")}
                  className={`p-4 rounded-lg border text-left transition-colors ${
                    selectedFormat === format.id
                      ? "border-primary bg-primary/5"
                      : "hover:bg-muted"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <format.icon className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <div className="font-medium">{format.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {format.description}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Include Options */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Include</label>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeRawData}
                  onChange={(e) => setIncludeRawData(e.target.checked)}
                  className="rounded border-input"
                />
                <span className="text-sm">Raw data from sources</span>
                <Badge variant="outline" className="text-xs">
                  Large file
                </Badge>
              </label>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={isExporting}>
            {isExporting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Download
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
