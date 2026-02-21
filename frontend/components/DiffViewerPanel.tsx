"use client";

import React, { useState, useEffect, useCallback } from "react";
import { patchService, PatchSession } from "../services/patchService";

interface DiffViewerPanelProps {
    sessionId: string;
    onResolved?: () => void;
}

export default function DiffViewerPanel({ sessionId, onResolved }: DiffViewerPanelProps) {
    const [patch, setPatch] = useState<PatchSession | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [isProcessing, setIsProcessing] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Limits and TTL
    const [isExpanded, setIsExpanded] = useState<boolean>(false);
    const [renderLimit, setRenderLimit] = useState<number>(50);
    const [minutesLeft, setMinutesLeft] = useState<number>(60);

    const fetchPatchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await patchService.fetchPatch(sessionId);
            setPatch(data);
        } catch (err: any) {
            setError(err.message || "Failed to fetch patch data.");
        } finally {
            setLoading(false);
        }
    }, [sessionId]);

    useEffect(() => {
        if (sessionId) {
            fetchPatchData();
        }
    }, [sessionId, fetchPatchData]);

    // TTL Countdown Effect
    useEffect(() => {
        if (patch?.status === "PENDING" && patch.created_at) {
            const calculateLeft = () => Math.max(0, 60 - Math.floor((Date.now() - patch.created_at * 1000) / 60000));
            setMinutesLeft(calculateLeft());
            const timer = setInterval(() => setMinutesLeft(calculateLeft()), 60000);
            return () => clearInterval(timer);
        }
    }, [patch]);

    const handleApply = async () => {
        if (!patch || patch.status !== "PENDING") return;
        setIsProcessing(true);
        setError(null);
        try {
            await patchService.applyPatch(sessionId);
            await fetchPatchData(); // Refetch to get updated status
            if (onResolved) onResolved();
        } catch (err: any) {
            setError(err.message || "Failed to apply patch.");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleDiscard = async () => {
        if (!patch || patch.status !== "PENDING") return;
        setIsProcessing(true);
        setError(null);
        try {
            await patchService.discardPatch(sessionId);
            await fetchPatchData(); // Refetch to get updated status
            if (onResolved) onResolved();
        } catch (err: any) {
            setError(err.message || "Failed to discard patch.");
        } finally {
            setIsProcessing(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-6 border rounded-md bg-gray-50 border-gray-200">
                <p className="text-gray-500 animate-pulse">Loading patch comparison...</p>
            </div>
        );
    }

    if (error && !patch) {
        return (
            <div className="p-4 border rounded-md bg-red-50 border-red-200 text-red-700">
                <h3 className="font-semibold mb-2">Error Loading Patch</h3>
                <p>{error}</p>
            </div>
        );
    }

    if (!patch) {
        return (
            <div className="p-4 border rounded-md bg-gray-50 border-gray-200 text-gray-500">
                No patch data available.
            </div>
        );
    }

    // Calculate status badge style
    const getBadgeStyle = (status: string) => {
        switch (status) {
            case "PENDING":
                return "bg-yellow-100 text-yellow-800 border-yellow-200";
            case "APPLIED":
                return "bg-green-100 text-green-800 border-green-200";
            case "DISCARDED":
                return "bg-gray-100 text-gray-800 border-gray-200";
            default:
                return "bg-gray-100 text-gray-800";
        }
    };

    const renderDiffLine = (line: string, index: number) => {
        let bgColor = "transparent";
        let textColor = "inherit";

        if (line.startsWith("+") && !line.startsWith("+++")) {
            bgColor = "#e6ffed"; // light green
            textColor = "#22863a";
        } else if (line.startsWith("-") && !line.startsWith("---")) {
            bgColor = "#ffeef0"; // light red
            textColor = "#b31d28";
        } else if (line.startsWith("@@")) {
            bgColor = "#f6f8fa";
            textColor = "#6a737d";
        }

        return (
            <div
                key={index}
                style={{
                    backgroundColor: bgColor,
                    color: textColor,
                    padding: "2px 8px",
                    fontFamily: "monospace",
                    fontSize: "13px",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-all",
                }}
            >
                {line || " "}
            </div>
        );
    };

    return (
        <div className="flex flex-col border border-gray-300 rounded-lg overflow-hidden bg-white shadow-sm mt-4 mb-4">
            {/* Header Section */}
            <div className="flex flex-row justify-between items-center p-3 border-b border-gray-200 bg-gray-50">
                <div className="flex flex-col space-y-1">
                    <h3 className="font-semibold text-gray-800 text-sm break-all">
                        📄 {patch.file_path.split(/[\\/]/).pop()}
                    </h3>
                    <span className="text-xs text-gray-400 font-mono">ID: {patch.session_id.split("-")[0]}...</span>
                </div>
                <div>
                    {patch.status === "PENDING" && (
                        <span className="mr-3 text-xs text-gray-400 font-medium tracking-wide">
                            🕒 Expires in {minutesLeft} min
                        </span>
                    )}
                    <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold border ${getBadgeStyle(
                            patch.status
                        )}`}
                    >
                        {patch.status}
                    </span>
                </div>
            </div>

            {/* Global Error Banner (for action failures) */}
            {error && (
                <div className="px-3 py-2 bg-red-100 text-red-700 text-xs font-semibold border-b border-red-200">
                    ⚠️ {error}
                </div>
            )}

            {/* Diff Body */}
            <div className="overflow-x-auto max-h-96 w-full border-b border-gray-200 bg-gray-50 flex flex-col relative scrollbar-thin scrollbar-thumb-gray-300">
                {patch.diff ? (
                    <div className="min-w-max py-2 flex-1">
                        {patch.diff.split("\n")
                            .slice(0, isExpanded ? renderLimit : 50)
                            .map((line, idx) => renderDiffLine(line, idx))}
                    </div>
                ) : (
                    <div className="p-4 text-center text-sm text-gray-500 italic">
                        Diff payload is empty or perfectly identical.
                    </div>
                )}
            </div>

            {/* Diff Pagination Controls (Large Payload Fix) */}
            {patch.diff && patch.diff.split("\n").length > 50 && (
                <div className="bg-gray-100 border-b border-gray-200 p-2 flex justify-center w-full">
                    {!isExpanded ? (
                        <button onClick={() => { setIsExpanded(true); setRenderLimit(500); }} className="text-xs text-blue-600 font-semibold hover:text-blue-800 transition-colors">
                            ⮟ Expand Diff ({patch.diff.split("\n").length - 50} lines hidden)
                        </button>
                    ) : patch.diff.split("\n").length > renderLimit ? (
                        <button onClick={() => setRenderLimit(prev => prev + 500)} className="text-xs text-blue-600 font-semibold hover:text-blue-800 transition-colors">
                            ⮟ Load Next 500 Lines ({patch.diff.split("\n").length - renderLimit} remaining)
                        </button>
                    ) : (
                        <button onClick={() => { setIsExpanded(false); setRenderLimit(50); }} className="text-xs text-gray-500 font-semibold hover:text-gray-700 transition-colors">
                            ⮝ Collapse Diff
                        </button>
                    )}
                </div>
            )}

            {/* Action Bar */}
            <div className="flex flex-row justify-end items-center p-3 space-x-3 bg-gray-100">
                <button
                    onClick={handleDiscard}
                    disabled={patch.status !== "PENDING" || isProcessing}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isProcessing ? "Processing..." : "Discard Patch"}
                </button>
                <button
                    onClick={handleApply}
                    disabled={patch.status !== "PENDING" || isProcessing}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
                >
                    {isProcessing ? "Processing..." : "Apply Patch"}
                </button>
            </div>
        </div>
    );
}
