import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  IconButton,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  Skeleton,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Stop as StopIcon,
  PlayArrow as PlayIcon,
  Notifications as NotificationIcon,
} from '@mui/icons-material'
import { monitoringApi, companiesApi } from '../../api/client'

const Monitoring = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState(0)
  const [scrapeUrl, setScrapeUrl] = useState('')

  const { data: monitoredCompanies, isLoading: loadingCompanies } = useQuery({
    queryKey: ['monitoring', 'companies'],
    queryFn: () => monitoringApi.getMonitoredCompanies(50).then((res) => res.data),
  })

  const { data: changes, isLoading: loadingChanges } = useQuery({
    queryKey: ['monitoring', 'changes'],
    queryFn: () => monitoringApi.getChanges({ limit: 50, days: 30 }).then((res) => res.data),
  })

  const disableMutation = useMutation({
    mutationFn: (id: string) => monitoringApi.disableMonitoring(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitoring', 'companies'] })
    },
  })

  const scrapeMutation = useMutation({
    mutationFn: () => monitoringApi.triggerScrape(undefined, scrapeUrl),
    onSuccess: () => {
      setScrapeUrl('')
      queryClient.invalidateQueries({ queryKey: ['monitoring'] })
    },
  })

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight={600} gutterBottom>
        Monitoring
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Monitor companies and track changes over time
      </Typography>

      {/* Quick Scrape */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Quick Scrape
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              placeholder="Enter URL to scrape (e.g., https://example.com)"
              value={scrapeUrl}
              onChange={(e) => setScrapeUrl(e.target.value)}
              fullWidth
              size="small"
            />
            <Button
              variant="contained"
              startIcon={scrapeMutation.isPending ? <CircularProgress size={20} /> : <AddIcon />}
              onClick={() => scrapeMutation.mutate()}
              disabled={scrapeMutation.isPending || !scrapeUrl}
            >
              Scrape
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        sx={{ mb: 3 }}
      >
        <Tab label={`Monitored Companies (${monitoredCompanies?.length || 0})`} />
        <Tab label={`Detected Changes (${changes?.length || 0})`} />
      </Tabs>

      {/* Monitored Companies */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          {loadingCompanies ? (
            Array.from({ length: 6 }).map((_, i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
              </Grid>
            ))
          ) : monitoredCompanies?.length > 0 ? (
            monitoredCompanies.map((company: any) => (
              <Grid item xs={12} sm={6} md={4} key={company.id}>
                <Card className="dashboard-card">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" fontWeight={600}>
                          {company.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {company.website}
                        </Typography>
                      </Box>
                      <Chip label="Monitoring" color="warning" size="small" />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }} noWrap>
                      {company.short_description || company.description || 'No description'}
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      {company.industry_classifications?.slice(0, 2).map((ind: any) => (
                        <Chip key={ind.id} label={ind.name} size="small" variant="outlined" />
                      ))}
                    </Box>

                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/companies/${company.id}`)}
                        >
                          <ViewIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => disableMutation.mutate(company.id)}
                          disabled={disableMutation.isPending}
                        >
                          <StopIcon />
                        </IconButton>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Last scraped: {company.last_scraped_at ? new Date(company.last_scraped_at).toLocaleDateString() : 'Never'}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Alert severity="info">
                No companies are currently being monitored.{' '}
                <Button onClick={() => navigate('/companies')}>Browse companies</Button> to start monitoring.
              </Alert>
            </Grid>
          )}
        </Grid>
      )}

      {/* Detected Changes */}
      {activeTab === 1 && (
        <Card>
          <CardContent sx={{ p: 0 }}>
            {loadingChanges ? (
              <Box sx={{ p: 3 }}>
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} variant="rectangular" height={60} sx={{ mb: 2, borderRadius: 1 }} />
                ))}
              </Box>
            ) : changes?.length > 0 ? (
              <List>
                {changes.map((change: any, index: number) => (
                  <ListItem
                    key={change.id || index}
                    divider
                    sx={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/companies/${change.company_id}`)}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body1" fontWeight={600}>
                            {change.company?.name || 'Unknown Company'}
                          </Typography>
                          <Chip
                            label={change.change_type.replace(/_/g, ' ')}
                            size="small"
                            color={getSeverityColor(change.severity) as any}
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          {change.description}
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            Detected: {new Date(change.detected_at).toLocaleString()}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <NotificationIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No changes detected
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Changes will appear here when monitored companies are updated
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default Monitoring