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
  Alert,
} from '@mui/material'
import {
  Business as BusinessIcon,
  Category as CategoryIcon,
  Inventory as ProductIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Notifications as NotificationIcon,
} from '@mui/icons-material'
import ReactECharts from 'echarts-for-react'

import { dashboardApi } from '../../api/client'

const StatCard = ({
  title,
  value,
  icon: Icon,
  color = 'primary.main',
  loading = false,
}: {
  title: string
  value: number | string
  icon: any
  color?: string
  loading?: boolean
}) => (
  <Card className="dashboard-card">
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Box
          sx={{
            p: 1.5,
            borderRadius: 2,
            bgcolor: `${color}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Icon sx={{ color, fontSize: 28 }} />
        </Box>
      </Box>
      {loading ? (
        <Skeleton variant="text" width={80} height={40} />
      ) : (
        <Typography variant="h4" fontWeight={700}>
          {value.toLocaleString()}
        </Typography>
      )}
      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
        {title}
      </Typography>
    </CardContent>
  </Card>
)

const Dashboard = () => {
  const { data: executiveData, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'executive'],
    queryFn: () => dashboardApi.getExecutive().then((res) => res.data),
  })

  if (error) {
    return (
      <Alert severity="error">
        Failed to load dashboard data. Please check if the backend is running.
      </Alert>
    )
  }

  const industryChartOption = {
    tooltip: { trigger: 'axis' as const, axisPointer: { type: 'shadow' as const } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: executiveData?.companies_by_industry?.slice(0, 10).map((i: any) => i.name) || [],
      axisLabel: { rotate: 45 },
    },
    yAxis: { type: 'value' as const },
    series: [
      {
        name: 'Companies',
        type: 'bar' as const,
        data: executiveData?.companies_by_industry?.slice(0, 10).map((i: any) => i.count) || [],
        itemStyle: { color: '#1976d2' },
      },
    ],
  }

  const countryChartOption = {
    tooltip: { trigger: 'item' as const },
    series: [
      {
        name: 'Companies by Country',
        type: 'pie' as const,
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' },
        },
        data: executiveData?.companies_by_country?.slice(0, 8).map((c: any) => ({
          value: c.count,
          name: c.country,
        })) || [],
      },
    ],
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>
        Executive Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Overview of company intelligence and monitoring metrics
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Total Companies"
            value={executiveData?.total_companies || 0}
            icon={BusinessIcon}
            color="#1976d2"
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Industries"
            value={executiveData?.total_industries || 0}
            icon={CategoryIcon}
            color="#9c27b0"
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Products"
            value={executiveData?.total_products || 0}
            icon={ProductIcon}
            color="#2e7d32"
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Active Monitoring"
            value={executiveData?.active_monitoring || 0}
            icon={TrendingUpIcon}
            color="#ed6c02"
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Recent Changes"
            value={executiveData?.recent_changes || 0}
            icon={NotificationIcon}
            color="#d32f2f"
            loading={isLoading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <StatCard
            title="Growth Signals"
            value={executiveData?.growth_signals || 0}
            icon={PeopleIcon}
            color="#0288d1"
            loading={isLoading}
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Companies by Industry
              </Typography>
              <ReactECharts option={industryChartOption} style={{ height: 400 }} />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Companies by Country
              </Typography>
              <ReactECharts option={countryChartOption} style={{ height: 400 }} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Recent Activity
              </Typography>
              <List>
                {executiveData?.recent_activity?.slice(0, 8).map((activity: any, index: number) => (
                  <ListItem
                    key={index}
                    divider
                    sx={{ px: 0 }}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {activity.company_name}
                          </Typography>
                          <Chip
                            label={activity.change_type.replace(/_/g, ' ')}
                            size="small"
                            color={
                              activity.severity === 'critical'
                                ? 'error'
                                : activity.severity === 'high'
                                ? 'warning'
                                : 'default'
                            }
                          />
                        </Box>
                      }
                      secondary={activity.description}
                    />
                  </ListItem>
                ))}
                {(!executiveData?.recent_activity || executiveData.recent_activity.length === 0) && (
                  <ListItem>
                    <ListItemText secondary="No recent activity" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Quick Stats
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Services
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      {executiveData?.total_services?.toLocaleString() || 0}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Customers
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      {executiveData?.total_customers?.toLocaleString() || 0}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Partners
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      {executiveData?.total_partners?.toLocaleString() || 0}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Domains
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      {executiveData?.total_domains?.toLocaleString() || 0}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard