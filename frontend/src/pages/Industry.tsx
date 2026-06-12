import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  Skeleton,
} from '@mui/material'
import {
  Business as BusinessIcon,
  Category as CategoryIcon,
  TrendingUp as TrendingUpIcon,
  ShowChart as ChartIcon,
} from '@mui/icons-material'
import ReactECharts from 'echarts-for-react'

import { dashboardApi, searchApi } from '../../api/client'

const Industry = () => {
  const { data: industryData, isLoading } = useQuery({
    queryKey: ['dashboard', 'industry'],
    queryFn: () => dashboardApi.getIndustry().then((res) => res.data),
  })

  const industryChartOption = {
    tooltip: { trigger: 'axis' as const, axisPointer: { type: 'shadow' as const } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: industryData?.companies_by_industry?.map((i: any) => i.name) || [],
      axisLabel: { rotate: 45 },
    },
    yAxis: { type: 'value' as const },
    series: [
      {
        name: 'Companies',
        type: 'bar' as const,
        data: industryData?.companies_by_industry?.map((i: any) => i.count) || [],
        itemStyle: { color: '#9c27b0' },
      },
    ],
  }

  const domainChartOption = {
    tooltip: { trigger: 'axis' as const, axisPointer: { type: 'shadow' as const } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: industryData?.companies_by_domain?.map((d: any) => d.name) || [],
      axisLabel: { rotate: 45 },
    },
    yAxis: { type: 'value' as const },
    series: [
      {
        name: 'Companies',
        type: 'bar' as const,
        data: industryData?.companies_by_domain?.map((d: any) => d.count) || [],
        itemStyle: { color: '#1976d2' },
      },
    ],
  }

  const growthChartOption = {
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['Total Companies', 'Monitored Companies'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: industryData?.growth_trends?.map((g: any) => g.period) || [],
    },
    yAxis: { type: 'value' as const },
    series: [
      {
        name: 'Total Companies',
        type: 'line' as const,
        data: industryData?.growth_trends?.map((g: any) => g.total_companies) || [],
        itemStyle: { color: '#1976d2' },
        smooth: true,
      },
      {
        name: 'Monitored Companies',
        type: 'line' as const,
        data: industryData?.growth_trends?.map((g: any) => g.monitored_companies) || [],
        itemStyle: { color: '#ed6c02' },
        smooth: true,
      },
    ],
  }

  const technologyChartOption = {
    tooltip: { trigger: 'item' as const },
    series: [
      {
        name: 'Technologies',
        type: 'pie' as const,
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, position: 'outside' },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
        },
        data: industryData?.technology_trends?.slice(0, 10).map((t: any) => ({
          value: t.count,
          name: t.name,
        })) || [],
      },
    ],
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>
        Industry Analysis
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Analyze companies by industry, domain, and technology
      </Typography>

      {/* Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: '#9c27b015',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <CategoryIcon sx={{ color: '#9c27b0', fontSize: 28 }} />
                </Box>
              </Box>
              <Typography variant="h4" fontWeight={700}>
                {industryData?.companies_by_industry?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Industries Covered
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: '#1976d215',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <BusinessIcon sx={{ color: '#1976d2', fontSize: 28 }} />
                </Box>
              </Box>
              <Typography variant="h4" fontWeight={700}>
                {industryData?.companies_by_domain?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Domains Identified
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: '#2e7d3215',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <ChartIcon sx={{ color: '#2e7d32', fontSize: 28 }} />
                </Box>
              </Box>
              <Typography variant="h4" fontWeight={700}>
                {industryData?.technology_trends?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Technologies Tracked
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card className="dashboard-card">
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: '#ed6c0215',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <TrendingUpIcon sx={{ color: '#ed6c02', fontSize: 28 }} />
                </Box>
              </Box>
              <Typography variant="h4" fontWeight={700}>
                {industryData?.growth_trends?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Periods Tracked
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Companies by Industry
              </Typography>
              <ReactECharts option={industryChartOption} style={{ height: 400 }} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Companies by Domain
              </Typography>
              <ReactECharts option={domainChartOption} style={{ height: 400 }} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Growth Trends
              </Typography>
              <ReactECharts option={growthChartOption} style={{ height: 400 }} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Top Technologies
              </Typography>
              <ReactECharts option={technologyChartOption} style={{ height: 400 }} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Industry List */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Industry Breakdown
          </Typography>
          <List>
            {industryData?.companies_by_industry?.map((industry: any, index: number) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body1" fontWeight={500}>
                        {industry.name}
                      </Typography>
                      <Chip label={`${industry.count} companies`} size="small" />
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Industry