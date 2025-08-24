"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, AreaChart, Area } from "recharts"

const performanceData = [
  { date: "2024-01-01", pnl: 0, cumulative: 0 },
  { date: "2024-01-02", pnl: 2.1, cumulative: 2.1 },
  { date: "2024-01-03", pnl: -0.8, cumulative: 1.3 },
  { date: "2024-01-04", pnl: 3.2, cumulative: 4.5 },
  { date: "2024-01-05", pnl: 1.7, cumulative: 6.2 },
  { date: "2024-01-06", pnl: -1.2, cumulative: 5.0 },
  { date: "2024-01-07", pnl: 2.8, cumulative: 7.8 },
  { date: "2024-01-08", pnl: 1.9, cumulative: 9.7 },
  { date: "2024-01-09", pnl: 0.6, cumulative: 10.3 },
  { date: "2024-01-10", pnl: 2.1, cumulative: 12.4 },
]

interface PerformanceChartProps {
  isArabic: boolean
}

export function PerformanceChart({ isArabic }: PerformanceChartProps) {
  const text = {
    en: {
      title: "Performance Overview",
      description: "Cumulative P&L and daily performance metrics",
      cumulativePnL: "Cumulative P&L (%)",
      dailyPnL: "Daily P&L (%)",
    },
    ar: {
      title: "نظرة عامة على الأداء",
      description: "الربح/الخسارة التراكمي ومقاييس الأداء اليومي",
      cumulativePnL: "الربح/الخسارة التراكمي (%)",
      dailyPnL: "الربح/الخسارة اليومي (%)",
    },
  }

  const t = isArabic ? text.ar : text.en

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="font-serif">{t.cumulativePnL}</CardTitle>
          <CardDescription>{t.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={{
              cumulative: {
                label: t.cumulativePnL,
                color: "hsl(var(--chart-1))",
              },
            }}
            className="h-[300px]"
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  type="monotone"
                  dataKey="cumulative"
                  stroke="hsl(var(--chart-1))"
                  fill="hsl(var(--chart-1))"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="font-serif">{t.dailyPnL}</CardTitle>
          <CardDescription>Daily performance breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={{
              pnl: {
                label: t.dailyPnL,
                color: "hsl(var(--chart-2))",
              },
            }}
            className="h-[300px]"
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="pnl"
                  stroke="hsl(var(--chart-2))"
                  strokeWidth={2}
                  dot={{ fill: "hsl(var(--chart-2))", strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  )
}
