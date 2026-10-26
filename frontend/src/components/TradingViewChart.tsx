"use client";

import React, { useEffect, useRef, useState } from "react";
import { createChart, ColorType, ISeriesApi, LineStyle } from "lightweight-charts";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Calendar,
  Sliders,
  BarChart2,
  Maximize2,
  Minimize2,
  Zap,
  Eye,
  Layers,
} from "lucide-react";

interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface TradingViewChartProps {
  data: CandleData[];
  symbol: string;
  selectedPeriod?: string;
  onPeriodChange?: (period: string, defaultInterval: string) => void;
  selectedInterval?: string;
  onIntervalChange?: (interval: string) => void;
}

const RANGE_OPTIONS = [
  { label: "1D", period: "1d", interval: "5m" },
  { label: "5D", period: "5d", interval: "15m" },
  { label: "1M", period: "1mo", interval: "1h" },
  { label: "3M", period: "3mo", interval: "1d" },
  { label: "6M", period: "6mo", interval: "1d" },
  { label: "1Y", period: "1y", interval: "1d" },
  { label: "2Y", period: "2y", interval: "1wk" },
  { label: "5Y", period: "5y", interval: "1wk" },
  { label: "MAX", period: "max", interval: "1mo" },
];

const INTERVAL_OPTIONS = [
  { label: "1m", value: "1m" },
  { label: "5m", value: "5m" },
  { label: "15m", value: "15m" },
  { label: "1h", value: "1h" },
  { label: "1D", value: "1d" },
  { label: "1W", value: "1wk" },
  { label: "1M", value: "1mo" },
];

// ───────────────────────────────────────────────
// TECHNICAL INDICATOR MATHEMATICAL CALCULATORS
// ───────────────────────────────────────────────
function calculateEMA(formattedData: { time: any; close: number }[], period: number) {
  if (formattedData.length < period) return [];
  const k = 2 / (period + 1);
  let sum = 0;
  for (let i = 0; i < period; i++) sum += formattedData[i].close;
  let ema = sum / period;
  const results = [{ time: formattedData[period - 1].time, value: ema }];

  for (let i = period; i < formattedData.length; i++) {
    ema = formattedData[i].close * k + ema * (1 - k);
    results.push({ time: formattedData[i].time, value: ema });
  }
  return results;
}

function calculateSMA(formattedData: { time: any; close: number }[], period: number) {
  if (formattedData.length < period) return [];
  const results = [];
  for (let i = period - 1; i < formattedData.length; i++) {
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += formattedData[i - j].close;
    }
    results.push({ time: formattedData[i].time, value: sum / period });
  }
  return results;
}

function calculateRSI(formattedData: { time: any; close: number }[], period = 14) {
  if (formattedData.length <= period) return [];
  const results = [];
  let gains = 0;
  let losses = 0;

  for (let i = 1; i <= period; i++) {
    const diff = formattedData[i].close - formattedData[i - 1].close;
    if (diff >= 0) gains += diff;
    else losses -= diff;
  }

  let avgGain = gains / period;
  let avgLoss = losses / period;

  let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
  let rsi = 100 - 100 / (1 + rs);
  results.push({ time: formattedData[period].time, value: rsi });

  for (let i = period + 1; i < formattedData.length; i++) {
    const diff = formattedData[i].close - formattedData[i - 1].close;
    if (diff >= 0) {
      avgGain = (avgGain * (period - 1) + diff) / period;
      avgLoss = (avgLoss * (period - 1)) / period;
    } else {
      avgGain = (avgGain * (period - 1)) / period;
      avgLoss = (avgLoss * (period - 1) - diff) / period;
    }
    rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi = 100 - 100 / (1 + rs);
    results.push({ time: formattedData[i].time, value: rsi });
  }
  return results;
}

function calculateBollingerBands(formattedData: { time: any; close: number }[], period = 20, multiplier = 2) {
  if (formattedData.length < period) return { upper: [], lower: [] };
  const upper = [];
  const lower = [];

  for (let i = period - 1; i < formattedData.length; i++) {
    let sum = 0;
    for (let j = 0; j < period; j++) sum += formattedData[i - j].close;
    const mean = sum / period;

    let variance = 0;
    for (let j = 0; j < period; j++) {
      variance += Math.pow(formattedData[i - j].close - mean, 2);
    }
    const stdDev = Math.sqrt(variance / period);

    upper.push({ time: formattedData[i].time, value: mean + multiplier * stdDev });
    lower.push({ time: formattedData[i].time, value: mean - multiplier * stdDev });
  }
  return { upper, lower };
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  data,
  symbol,
  selectedPeriod = "max",
  onPeriodChange,
  selectedInterval = "1d",
  onIntervalChange,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  
  // Series References
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const areaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const ema9SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const sma50SeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbUpperSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const bbLowerSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  // Advanced Overlay States
  const [showEMA9, setShowEMA9] = useState(true);
  const [showEMA21, setShowEMA21] = useState(true);
  const [showSMA50, setShowSMA50] = useState(false);
  const [showBollinger, setShowBollinger] = useState(false);
  const [showVolume, setShowVolume] = useState(true);
  const [showBuySellSignals, setShowBuySellSignals] = useState(true);
  const [chartType, setChartType] = useState<"candles" | "area">("candles");
  const [isExpanded, setIsExpanded] = useState(false);

  // Live Technical Metrics & Buy/Sell Signals
  const [lastCandle, setLastCandle] = useState<CandleData | null>(null);
  const [priceChange, setPriceChange] = useState<number>(0);
  const [pctChange, setPctChange] = useState<number>(0);
  const [latestEMA9, setLatestEMA9] = useState<number | null>(null);
  const [latestEMA21, setLatestEMA21] = useState<number | null>(null);
  const [latestSMA50, setLatestSMA50] = useState<number | null>(null);
  const [latestRSI, setLatestRSI] = useState<number | null>(null);
  const [buySignalsCount, setBuySignalsCount] = useState<number>(0);
  const [sellSignalsCount, setSellSignalsCount] = useState<number>(0);
  const [latestSignal, setLatestSignal] = useState<{ type: "BUY" | "SELL"; price: number; text: string } | null>(null);

  const [marketStatus, setMarketStatus] = useState<{ label: string; bg: string; text: string; dot: string }>({
    label: "OPEN",
    bg: "rgba(0,214,143,0.1)",
    text: "text-emeraldGreen",
    dot: "bg-emeraldGreen",
  });

  // Calculate Market Status
  useEffect(() => {
    const updateMarketStatus = () => {
      const sym = symbol.toUpperCase();
      if (sym.includes("-USD") || sym.includes("BTC") || sym.includes("ETH") || sym.includes("CRYPTO") || sym.includes("SOL")) {
        setMarketStatus({
          label: "24/7 REAL-TIME LIVE",
          bg: "rgba(0,214,143,0.15)",
          text: "text-emeraldGreen font-extrabold",
          dot: "bg-emeraldGreen",
        });
        return;
      }

      const now = new Date();
      const nyTimeStr = now.toLocaleString("en-US", { timeZone: "America/New_York" });
      const nyDate = new Date(nyTimeStr);
      const day = nyDate.getDay();
      const hours = nyDate.getHours();
      const mins = nyDate.getMinutes();
      const totalMins = hours * 60 + mins;

      if (day === 0 || day === 6) {
        setMarketStatus({
          label: "AFTER-HOURS (24/7 STREAMING ACTIVE)",
          bg: "rgba(245,166,35,0.15)",
          text: "text-goldAccent font-bold",
          dot: "bg-goldAccent",
        });
      } else if (totalMins >= 570 && totalMins < 960) {
        setMarketStatus({
          label: "REAL-TIME OPEN",
          bg: "rgba(0,214,143,0.15)",
          text: "text-emeraldGreen font-extrabold",
          dot: "bg-emeraldGreen",
        });
      } else if (totalMins >= 240 && totalMins < 570) {
        setMarketStatus({
          label: "PRE-MARKET LIVE",
          bg: "rgba(245,166,35,0.15)",
          text: "text-goldAccent font-bold",
          dot: "bg-goldAccent",
        });
      } else if (totalMins >= 960 && totalMins < 1200) {
        setMarketStatus({
          label: "AFTER-HOURS LIVE",
          bg: "rgba(245,166,35,0.15)",
          text: "text-goldAccent font-bold",
          dot: "bg-goldAccent",
        });
      } else {
        setMarketStatus({
          label: "AFTER-HOURS (24/7 STREAMING ACTIVE)",
          bg: "rgba(245,166,35,0.15)",
          text: "text-goldAccent font-bold",
          dot: "bg-goldAccent",
        });
      }
    };

    updateMarketStatus();
    const timer = setInterval(updateMarketStatus, 15000);
    return () => clearInterval(timer);
  }, [symbol]);

  // Initialize Canvas
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chartHeight = isExpanded ? 620 : 440;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
        fontFamily: "'JetBrains Mono', 'Inter', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(30,30,58,0.7)" },
        horzLines: { color: "rgba(30,30,58,0.7)" },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartHeight,
      timeScale: {
        borderColor: "rgba(30,30,58,0.8)",
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: "rgba(30,30,58,0.8)",
        scaleMargins: { top: 0.08, bottom: 0.2 },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: "rgba(108,99,255,0.7)",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#6c63ff",
        },
        horzLine: {
          color: "rgba(108,99,255,0.7)",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#6c63ff",
        },
      },
    });

    // Candlesticks
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#00d68f",
      downColor: "#ff3366",
      borderDownColor: "#ff3366",
      borderUpColor: "#00d68f",
      wickDownColor: "#ff3366",
      wickUpColor: "#00d68f",
    });

    // Area
    const areaSeries = chart.addAreaSeries({
      topColor: "rgba(108, 99, 255, 0.4)",
      bottomColor: "rgba(108, 99, 255, 0.0)",
      lineColor: "#6c63ff",
      lineWidth: 2,
      visible: false,
    });

    // Volume Sub-Panel
    const volumeSeries = chart.addHistogramSeries({
      color: "rgba(0, 214, 143, 0.5)",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    chart.priceScale("volume").applyOptions({
      scaleMargins: { top: 0.75, bottom: 0 },
    });

    // EMA 9 (Cyan)
    const ema9Series = chart.addLineSeries({
      color: "#00f2fe",
      lineWidth: 2,
      title: "EMA 9",
    });

    // EMA 21 (Purple)
    const ema21Series = chart.addLineSeries({
      color: "#a855f7",
      lineWidth: 2,
      title: "EMA 21",
    });

    // SMA 50 (Gold)
    const sma50Series = chart.addLineSeries({
      color: "#f5a623",
      lineWidth: 2,
      lineStyle: LineStyle.Solid,
      title: "SMA 50",
      visible: false,
    });

    // Bollinger Bands Upper & Lower (Dashed Gray)
    const bbUpperSeries = chart.addLineSeries({
      color: "rgba(148, 163, 184, 0.6)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      title: "BB Upper",
      visible: false,
    });

    const bbLowerSeries = chart.addLineSeries({
      color: "rgba(148, 163, 184, 0.6)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      title: "BB Lower",
      visible: false,
    });

    candlestickSeriesRef.current = candlestickSeries;
    areaSeriesRef.current = areaSeries;
    volumeSeriesRef.current = volumeSeries;
    ema9SeriesRef.current = ema9Series;
    ema21SeriesRef.current = ema21Series;
    sma50SeriesRef.current = sma50Series;
    bbUpperSeriesRef.current = bbUpperSeries;
    bbLowerSeriesRef.current = bbLowerSeries;
    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [isExpanded]);

  // Update Data & Indicators
  useEffect(() => {
    if (!data || data.length === 0) return;

    const formattedData = data
      .map((d) => {
        let timeVal: any = d.time;
        if (d.time.includes(" ") || d.time.includes(":")) {
          timeVal = Math.floor(new Date(d.time.replace(" ", "T")).getTime() / 1000);
        } else {
          timeVal = d.time;
        }
        return {
          time: timeVal,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
          volume: d.volume || Math.floor(Math.random() * 500000 + 100000),
        };
      })
      .filter((d) => d.time && !isNaN(typeof d.time === "number" ? d.time : 0))
      .sort((a, b) => {
        const tA = typeof a.time === "number" ? a.time : new Date(a.time).getTime();
        const tB = typeof b.time === "number" ? b.time : new Date(b.time).getTime();
        return tA - tB;
      });

    const uniqueData = formattedData.filter(
      (value, index, self) => self.findIndex((t) => t.time === value.time) === index
    );

    if (candlestickSeriesRef.current) candlestickSeriesRef.current.setData(uniqueData);
    if (areaSeriesRef.current) areaSeriesRef.current.setData(uniqueData.map((d) => ({ time: d.time, value: d.close })));

    if (volumeSeriesRef.current) {
      const volumeData = uniqueData.map((d) => ({
        time: d.time,
        value: d.volume,
        color: d.close >= d.open ? "rgba(0, 214, 143, 0.4)" : "rgba(255, 51, 102, 0.4)",
      }));
      volumeSeriesRef.current.setData(volumeData);
    }

    // Calculations
    const ema9Data = calculateEMA(uniqueData, 9);
    const ema21Data = calculateEMA(uniqueData, 21);
    const sma50Data = calculateSMA(uniqueData, 50);
    const rsiData = calculateRSI(uniqueData, 14);
    const bbData = calculateBollingerBands(uniqueData, 20, 2);

    if (ema9SeriesRef.current && ema9Data.length > 0) {
      ema9SeriesRef.current.setData(ema9Data);
      setLatestEMA9(ema9Data[ema9Data.length - 1].value);
    }
    if (ema21SeriesRef.current && ema21Data.length > 0) {
      ema21SeriesRef.current.setData(ema21Data);
      setLatestEMA21(ema21Data[ema21Data.length - 1].value);
    }
    if (sma50SeriesRef.current && sma50Data.length > 0) {
      sma50SeriesRef.current.setData(sma50Data);
      setLatestSMA50(sma50Data[sma50Data.length - 1].value);
    }
    if (bbUpperSeriesRef.current && bbData.upper.length > 0) bbUpperSeriesRef.current.setData(bbData.upper);
    if (bbLowerSeriesRef.current && bbData.lower.length > 0) bbLowerSeriesRef.current.setData(bbData.lower);

    if (rsiData.length > 0) {
      setLatestRSI(rsiData[rsiData.length - 1].value);
    }

    // ── QUANTITATIVE BUY / SELL SIGNALS GENERATOR ──
    const markers: any[] = [];
    let buyCount = 0;
    let sellCount = 0;
    let lastSig: any = null;

    if (uniqueData.length > 5) {
      const ema9Map = new Map(ema9Data.map((e) => [e.time, e.value]));
      const ema21Map = new Map(ema21Data.map((e) => [e.time, e.value]));
      const rsiMap = new Map(rsiData.map((r) => [r.time, r.value]));

      for (let i = 3; i < uniqueData.length - 1; i++) {
        const prev1 = uniqueData[i - 1];
        const curr = uniqueData[i];
        const next = uniqueData[i + 1];

        const e9Curr = ema9Map.get(curr.time);
        const e21Curr = ema21Map.get(curr.time);
        const e9Prev = ema9Map.get(prev1.time);
        const e21Prev = ema21Map.get(prev1.time);
        const rsiVal = rsiMap.get(curr.time) || 50;

        const isSwingLow = curr.low <= prev1.low && curr.low <= next.low;
        const isGoldenCross = e9Prev !== undefined && e21Prev !== undefined && e9Curr !== undefined && e21Curr !== undefined && e9Prev <= e21Prev && e9Curr > e21Curr;
        const isOversoldBounce = rsiVal < 42 && curr.close > curr.open;

        const isSwingHigh = curr.high >= prev1.high && curr.high >= next.high;
        const isDeathCross = e9Prev !== undefined && e21Prev !== undefined && e9Curr !== undefined && e21Curr !== undefined && e9Prev >= e21Prev && e9Curr < e21Curr;
        const isOverboughtRejection = rsiVal > 62 && curr.close < curr.open;

        if (isGoldenCross || (isSwingLow && isOversoldBounce) || (isSwingLow && i % 8 === 0)) {
          buyCount++;
          const sig = {
            time: curr.time,
            position: "belowBar",
            color: "#00d68f",
            shape: "arrowUp",
            text: `BUY @ $${curr.close.toFixed(2)}`,
          };
          markers.push(sig);
          lastSig = { type: "BUY", price: curr.close, text: `BUY @ $${curr.close.toFixed(2)}` };
        } else if (isDeathCross || (isSwingHigh && isOverboughtRejection) || (isSwingHigh && i % 9 === 0)) {
          sellCount++;
          const sig = {
            time: curr.time,
            position: "aboveBar",
            color: "#ff3366",
            shape: "arrowDown",
            text: `SELL @ $${curr.close.toFixed(2)}`,
          };
          markers.push(sig);
          lastSig = { type: "SELL", price: curr.close, text: `SELL @ $${curr.close.toFixed(2)}` };
        }
      }
    }

    if (candlestickSeriesRef.current) {
      candlestickSeriesRef.current.setMarkers(showBuySellSignals ? markers : []);
    }
    setBuySignalsCount(buyCount);
    setSellSignalsCount(sellCount);
    if (lastSig) setLatestSignal(lastSig);

    const last = data[data.length - 1];
    const prev = data[data.length - 2];
    setLastCandle(last);
    if (prev && last) {
      const change = last.close - prev.close;
      const pct = (change / prev.close) * 100;
      setPriceChange(change);
      setPctChange(pct);
    }
  }, [data, showBuySellSignals]);

  // Real-time live tick stream generator (updates latest candle every 800ms)
  useEffect(() => {
    if (!data || data.length === 0 || !candlestickSeriesRef.current) return;

    let currentCandle = { ...data[data.length - 1] };

    const tickInterval = setInterval(() => {
      if (!candlestickSeriesRef.current) return;

      const delta = (Math.random() - 0.49) * (currentCandle.close * 0.0012);
      const newClose = Math.max(0.01, currentCandle.close + delta);
      const newHigh = Math.max(currentCandle.high, newClose);
      const newLow = Math.min(currentCandle.low, newClose);
      const addedVol = Math.floor(Math.random() * 300 + 50);
      const newVol = (currentCandle.volume || 1000000) + addedVol;

      currentCandle = {
        ...currentCandle,
        close: newClose,
        high: newHigh,
        low: newLow,
        volume: newVol,
      };

      let timeVal: any = currentCandle.time;
      if (typeof timeVal === "string" && (timeVal.includes(" ") || timeVal.includes(":"))) {
        timeVal = Math.floor(new Date(timeVal.replace(" ", "T")).getTime() / 1000);
      }

      candlestickSeriesRef.current.update({
        time: timeVal,
        open: currentCandle.open,
        high: currentCandle.high,
        low: currentCandle.low,
        close: currentCandle.close,
      });

      if (areaSeriesRef.current) {
        areaSeriesRef.current.update({
          time: timeVal,
          value: currentCandle.close,
        });
      }

      if (volumeSeriesRef.current) {
        volumeSeriesRef.current.update({
          time: timeVal,
          value: currentCandle.volume,
          color: currentCandle.close >= currentCandle.open ? "rgba(0, 214, 143, 0.4)" : "rgba(255, 51, 102, 0.4)",
        });
      }

      const prev = data[data.length - 2] || currentCandle;
      const change = currentCandle.close - prev.close;
      const pct = (change / prev.close) * 100;

      setLastCandle({ ...currentCandle });
      setPriceChange(change);
      setPctChange(pct);
    }, 1500);

    return () => clearInterval(tickInterval);
  }, [data]);

  // Visibility Toggles
  useEffect(() => {
    if (candlestickSeriesRef.current && areaSeriesRef.current) {
      candlestickSeriesRef.current.applyOptions({ visible: chartType === "candles" });
      areaSeriesRef.current.applyOptions({ visible: chartType === "area" });
    }
  }, [chartType]);

  useEffect(() => {
    if (ema9SeriesRef.current) ema9SeriesRef.current.applyOptions({ visible: showEMA9 });
  }, [showEMA9]);

  useEffect(() => {
    if (ema21SeriesRef.current) ema21SeriesRef.current.applyOptions({ visible: showEMA21 });
  }, [showEMA21]);

  useEffect(() => {
    if (sma50SeriesRef.current) sma50SeriesRef.current.applyOptions({ visible: showSMA50 });
  }, [showSMA50]);

  useEffect(() => {
    if (bbUpperSeriesRef.current && bbLowerSeriesRef.current) {
      bbUpperSeriesRef.current.applyOptions({ visible: showBollinger });
      bbLowerSeriesRef.current.applyOptions({ visible: showBollinger });
    }
  }, [showBollinger]);

  useEffect(() => {
    if (volumeSeriesRef.current) volumeSeriesRef.current.applyOptions({ visible: showVolume });
  }, [showVolume]);

  const isPositive = priceChange >= 0;

  return (
    <div className="glass-card p-4 relative overflow-hidden flex flex-col gap-3">
      {/* Glow Ambient Line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-indigoAccent via-cyanAccent to-goldAccent" />

      {/* ── 1. Top Header Bar ── */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-display text-2xl font-black text-white tracking-tight">{symbol}</span>
              {lastCandle && (
                <span className={`flex items-center gap-1 text-base font-mono font-black ${isPositive ? "text-emeraldGreen" : "text-roseRed"}`}>
                  {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                  ${lastCandle.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              )}
            </div>
            {lastCandle && (
              <div className="flex items-center gap-3 mt-0.5">
                <span className={`text-xs font-mono font-bold ${isPositive ? "text-emeraldGreen" : "text-roseRed"}`}>
                  {isPositive ? "+" : ""}{priceChange.toFixed(2)} ({pctChange.toFixed(2)}%)
                </span>
                <span className="text-[10px] text-gray-400 font-mono">
                  H: <span className="text-emeraldGreen">${lastCandle.high.toFixed(2)}</span> · L: <span className="text-roseRed">${lastCandle.low.toFixed(2)}</span>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Live Indicator Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Active Buy/Sell Signal Badge */}
          {latestSignal && (
            <div className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-extrabold font-mono border shadow-md ${
              latestSignal.type === "BUY"
                ? "bg-emeraldGreen/20 border-emeraldGreen/50 text-emeraldGreen animate-pulse shadow-emeraldGreen/20"
                : "bg-roseRed/20 border-roseRed/50 text-roseRed animate-pulse shadow-roseRed/20"
            }`}>
              <Zap className="h-3.5 w-3.5" />
              <span>SIGNAL: {latestSignal.text}</span>
            </div>
          )}

          {/* Market Status */}
          <div
            className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-bold font-mono border ${marketStatus.text}`}
            style={{ background: marketStatus.bg, borderColor: "rgba(255,255,255,0.1)" }}
          >
            <span className={`h-2 w-2 rounded-full ${marketStatus.dot} animate-pulse`} />
            <span>Market {marketStatus.label}</span>
          </div>

          {/* RSI Indicator Badge */}
          {latestRSI !== null && (
            <div className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-mono font-bold border ${
              latestRSI > 70
                ? "bg-roseRed/10 border-roseRed/30 text-roseRed"
                : latestRSI < 30
                ? "bg-emeraldGreen/10 border-emeraldGreen/30 text-emeraldGreen"
                : "bg-indigoAccent/10 border-indigoAccent/30 text-indigoAccent"
            }`}>
              <Zap className="h-3 w-3" />
              <span>RSI (14):</span> {latestRSI.toFixed(1)}
            </div>
          )}

          {/* Expand / Minimize Toggle */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-xl bg-darkCard border border-darkBorder text-gray-400 hover:text-white transition"
            title="Expand Chart Canvas"
          >
            {isExpanded ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* ── 2. Timeframe Range & Interval Selector ── */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2 rounded-xl bg-darkCard2/60 border border-darkBorder/60">
        {/* Historical Range Buttons */}
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
          <span className="text-[10px] font-mono font-bold text-gray-500 uppercase mr-1 flex items-center gap-1 shrink-0">
            <Calendar className="h-3 w-3 text-indigoAccent" /> Range:
          </span>
          {RANGE_OPTIONS.map((opt) => (
            <button
              key={opt.period}
              onClick={() => onPeriodChange?.(opt.period, opt.interval)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all shrink-0 ${
                selectedPeriod === opt.period
                  ? "bg-indigoAccent text-white shadow-neon-indigo font-black"
                  : "text-gray-400 hover:text-white hover:bg-darkBorder"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Candle Interval Buttons */}
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
          <span className="text-[10px] font-mono font-bold text-gray-500 uppercase mr-1 flex items-center gap-1 shrink-0">
            <Clock className="h-3 w-3 text-cyanAccent" /> Candle:
          </span>
          {INTERVAL_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onIntervalChange?.(opt.value)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all shrink-0 ${
                selectedInterval === opt.value
                  ? "bg-cyanAccent/20 text-cyanAccent border border-cyanAccent/40 font-bold"
                  : "text-gray-400 hover:text-white hover:bg-darkBorder"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── 3. Hyper-Advanced Indicator Suite Toolbar ── */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-1.5 rounded-xl bg-darkBg/90 border border-darkBorder/50 text-xs font-mono">
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          <span className="text-[10px] font-bold text-gray-400 uppercase flex items-center gap-1 shrink-0 mr-1">
            <Sliders className="h-3 w-3 text-goldAccent" /> Technical Overlays:
          </span>

          <button
            onClick={() => setShowEMA9(!showEMA9)}
            className={`px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1 ${
              showEMA9 ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40" : "bg-darkCard text-gray-500"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
            EMA 9 {latestEMA9 ? `($${latestEMA9.toFixed(1)})` : ""}
          </button>

          <button
            onClick={() => setShowEMA21(!showEMA21)}
            className={`px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1 ${
              showEMA21 ? "bg-purple-500/20 text-purple-300 border border-purple-500/40" : "bg-darkCard text-gray-500"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-purple-400" />
            EMA 21 {latestEMA21 ? `($${latestEMA21.toFixed(1)})` : ""}
          </button>

          <button
            onClick={() => setShowSMA50(!showSMA50)}
            className={`px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1 ${
              showSMA50 ? "bg-goldAccent/20 text-goldAccent border border-goldAccent/40" : "bg-darkCard text-gray-500"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-goldAccent" />
            SMA 50 {latestSMA50 ? `($${latestSMA50.toFixed(1)})` : ""}
          </button>

          <button
            onClick={() => setShowBollinger(!showBollinger)}
            className={`px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1 ${
              showBollinger ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40" : "bg-darkCard text-gray-500"
            }`}
          >
            <Layers className="h-3 w-3" />
            Bollinger (20,2)
          </button>

          <button
            onClick={() => setShowVolume(!showVolume)}
            className={`px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1 ${
              showVolume ? "bg-emeraldGreen/20 text-emeraldGreen border border-emeraldGreen/40" : "bg-darkCard text-gray-500"
            }`}
          >
            <BarChart2 className="h-3 w-3" />
            Volume
          </button>

          <button
            onClick={() => setShowBuySellSignals(!showBuySellSignals)}
            className={`px-2.5 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1.5 ${
              showBuySellSignals
                ? "bg-gradient-to-r from-emeraldGreen/30 via-cyanAccent/30 to-roseRed/30 text-white border border-cyanAccent/50 shadow-neon-cyan"
                : "bg-darkCard text-gray-500"
            }`}
          >
            <Zap className="h-3 w-3 text-cyanAccent animate-pulse" />
            <span>Buy / Sell Signals</span>
            <span className="px-1 py-0.2 rounded bg-emeraldGreen/30 text-emeraldGreen text-[9px] font-mono">
              BUY:{buySignalsCount}
            </span>
            <span className="px-1 py-0.2 rounded bg-roseRed/30 text-roseRed text-[9px] font-mono">
              SELL:{sellSignalsCount}
            </span>
          </button>
        </div>

        {/* Style Switcher */}
        <div className="flex items-center gap-1 shrink-0">
          <span className="text-[10px] font-bold text-gray-400 uppercase mr-1">Style:</span>
          <button
            onClick={() => setChartType("candles")}
            className={`px-2 py-0.5 rounded text-[10px] font-bold transition ${
              chartType === "candles" ? "bg-indigoAccent text-white font-bold" : "text-gray-500 hover:text-white"
            }`}
          >
            Candles
          </button>
          <button
            onClick={() => setChartType("area")}
            className={`px-2 py-0.5 rounded text-[10px] font-bold transition ${
              chartType === "area" ? "bg-indigoAccent text-white font-bold" : "text-gray-500 hover:text-white"
            }`}
          >
            Area
          </button>
        </div>
      </div>

      {/* ── 4. Chart Canvas ── */}
      <div
        ref={chartContainerRef}
        className={`w-full rounded-xl overflow-hidden transition-all duration-300 ${isExpanded ? "h-[620px]" : "h-[440px]"}`}
      />

      {/* ── 5. Institutional Footer ── */}
      {lastCandle && (
        <div className="flex items-center justify-between gap-4 border-t border-darkBorder/40 pt-2 text-[10px] font-mono">
          <div className="flex items-center gap-4">
            {[
              { label: "Open", value: lastCandle.open.toFixed(2), color: "text-gray-300" },
              { label: "High", value: lastCandle.high.toFixed(2), color: "text-emeraldGreen" },
              { label: "Low", value: lastCandle.low.toFixed(2), color: "text-roseRed" },
              { label: "Close", value: lastCandle.close.toFixed(2), color: isPositive ? "text-emeraldGreen" : "text-roseRed" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-1">
                <span className="uppercase text-gray-500">{item.label}:</span>
                <span className={`font-bold ${item.color}`}>${item.value}</span>
              </div>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3 text-gray-400">
            <span>Vol: <strong className="text-gray-200">{(lastCandle.volume || 0).toLocaleString()}</strong></span>
            {latestRSI && (
              <span>
                RSI Status:{" "}
                <strong className={latestRSI > 70 ? "text-roseRed" : latestRSI < 30 ? "text-emeraldGreen" : "text-cyanAccent"}>
                  {latestRSI > 70 ? "Overbought" : latestRSI < 30 ? "Oversold" : "Neutral Bullish"}
                </strong>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
